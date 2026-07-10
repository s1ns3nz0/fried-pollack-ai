from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CLIENT_ID_PLACEHOLDER = "00000000-0000-0000-0000-000000000000"


def test_deploy_layout_contains_argocd_and_kagent_resources():
    expected = [
        "deploy/base/kustomization.yaml",
        "deploy/base/toolserver-deploy.yaml",
        "deploy/base/kagent-agent.yaml",
        "deploy/base/kagent-mcpserver.yaml",
        "deploy/base/kagent-modelconfig.yaml",
        "deploy/overlays/aks/kustomization.yaml",
        "deploy/argocd/root-app.yaml",
        "deploy/argocd/apps/kagent-platform.yaml",
        "deploy/argocd/apps/fried-pollack.yaml",
    ]
    # Azure IaC (bicep) and the sim/red provisioning script were extracted to the
    # pollak-infra repo; only app-layer kustomize/argocd manifests live here now.

    for relpath in expected:
        assert (ROOT / relpath).exists(), relpath


def test_aks_overlay_tracks_acr_image_with_immutable_tag():
    overlay = yaml.safe_load((ROOT / "deploy/overlays/aks/kustomization.yaml").read_text())

    assert overlay["images"][0]["name"] == "fried-pollack-ai"
    assert overlay["images"][0]["newName"] == "dahredacrr0710a.azurecr.io/fried-pollack-ai"
    assert overlay["images"][0]["newTag"] == "9db7585"


def test_workload_identity_client_id_is_injected_by_bootstrap():
    service_account = yaml.safe_load((ROOT / "deploy/base/serviceaccount.yaml").read_text())
    overlay = yaml.safe_load((ROOT / "deploy/overlays/aks/kustomization.yaml").read_text())

    assert service_account["metadata"]["annotations"]["azure.workload.identity/client-id"] == CLIENT_ID_PLACEHOLDER
    assert overlay["patches"][0]["patch"].endswith(f"value: {CLIENT_ID_PLACEHOLDER}")


def test_bootstrap_uses_existing_azure_cli_login_for_kubectl():
    bootstrap = (ROOT / "scripts/bootstrap-red-agent.sh").read_text()

    credentials_index = bootstrap.index("az aks get-credentials")
    kubelogin_index = bootstrap.index("kubelogin convert-kubeconfig")
    first_kubectl_index = bootstrap.index("kubectl create namespace")

    assert credentials_index < kubelogin_index < first_kubectl_index
    assert "--login azurecli" in bootstrap[kubelogin_index:first_kubectl_index]


def test_kagent_agent_and_toolserver_run_on_red_node_pool():
    rendered = list(yaml.safe_load_all((ROOT / "deploy/base/kagent-agent.yaml").read_text()))
    agent = rendered[0]
    deployment = agent["spec"]["declarative"]["deployment"]

    assert deployment["nodeSelector"] == {"workload": "red-agent"}
    assert deployment["tolerations"][0] == {
        "key": "workload",
        "operator": "Equal",
        "value": "red-agent",
        "effect": "NoSchedule",
    }

    docs = list(yaml.safe_load_all((ROOT / "deploy/base/toolserver-deploy.yaml").read_text()))
    deploy = next(doc for doc in docs if doc["kind"] == "Deployment")
    pod_spec = deploy["spec"]["template"]["spec"]

    assert pod_spec["nodeSelector"] == {"workload": "red-agent"}


def test_deploy_and_ci_yaml_parse():
    paths = list((ROOT / "deploy").rglob("*.yaml")) + [ROOT / ".github/workflows/ci.yml"]

    for path in paths:
        with path.open() as fh:
            assert list(yaml.safe_load_all(fh)), path
