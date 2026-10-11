"""Use the installed Cho loader through a pinned local file resolver."""
EVENTS = {"left_hand": 1, "right_hand": 2}


def load_runtime():
    from worker_common_004 import load_runtime as measured_runtime
    np, mne, _, pools, _, Config, preprocess = measured_runtime()
    from scipy.io import savemat
    from moabb.datasets.gigadb import Cho2017
    from moabb.datasets.preprocessing import SetRawAnnotations
    return np, mne, pools, Config, preprocess, savemat, Cho2017, SetRawAnnotations


def local_raw(path, subject, Dataset, Annotator):
    class PinnedLocalCho(Dataset):
        def data_path(self, selected, **kwargs):
            if selected != subject:
                raise ValueError("unexpected Cho subject request")
            return str(path)
    dataset = PinnedLocalCho()
    if dataset.event_id != EVENTS or list(dataset.interval) != [0, 3]:
        raise ValueError("installed Cho event/interval contract differs")
    data = dataset._get_single_subject_data(subject)
    if set(data) != {"0"} or set(data["0"]) != {"0"}:
        raise ValueError("single Cho session/run required")
    annotator = Annotator(dataset.event_id, interval=dataset.interval)
    return annotator.transform(data["0"]["0"])


def synthetic_fixture(path, np, savemat):
    samples = np.arange(8192) / 512
    amplitudes = np.arange(1, 69)
    left = np.outer(amplitudes, np.sin(2 * np.pi * 12 * samples))
    right = np.outer(amplitudes, np.cos(2 * np.pi * 13 * samples))
    events = np.zeros((1, 8192))
    events[0, [1024, 4096]] = 1
    savemat(path, {"eeg": {"imagery_left": left, "imagery_right": right, "imagery_event": events, "srate": 512}})
    return left, right, events


def build_artifact(raw, Config, configuration, preprocess):
    return preprocess([("0", "0", raw)], event_id=EVENTS, label_map={name: name for name in EVENTS}, config=configuration(Config))
