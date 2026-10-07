from backend.models import RunDetail, RunSummary, Step
def test_models_import():
    assert RunDetail is not None
    assert RunSummary is not None
    assert Step is not None
