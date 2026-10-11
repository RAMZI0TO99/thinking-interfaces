"""Direct local loading matches installed BNCI loader; no scientific imports yet."""

EVENTS = {"left_hand": 1, "right_hand": 2, "feet": 3, "tongue": 4}
CHANNELS = ["Fz", "FC3", "FC1", "FCz", "FC2", "FC4", "C5", "C3", "C1", "Cz", "C2", "C4", "C6", "CP3", "CP1", "CPz", "CP2", "CP4", "P1", "Pz", "P2", "POz", "EOG1", "EOG2", "EOG3"]
TYPES = ["eeg"] * 22 + ["eog"] * 3


def load_bci_runtime():
    from worker_common_004 import load_runtime
    np, mne, _, pools, _, Config, _ = load_runtime()
    from scipy.io import savemat
    from moabb.datasets.bnci.base import _convert_mi
    from moabb.datasets.preprocessing import SetRawAnnotations
    from data.profile_a import preprocess_run
    return np, mne, pools, Config, savemat, _convert_mi, SetRawAnnotations, preprocess_run


def local_runs(path, subject, convert, Annotator):
    raws, events = convert(str(path), CHANNELS, TYPES, dataset_code="BNCI2014-001", subject_id=subject,
                           artifact_handling="ignore", artifact_interval=(2, 6))
    if events != EVENTS:
        raise ValueError("BCI loader event mapping differs")
    annotator = Annotator(EVENTS, interval=[2, 6])
    return [annotator.transform(raw) for raw in raws]


def build_arrays(sessions, config, np, preprocess):
    # This is the collection schema of frozen preprocess_subject, using its
    # unchanged preprocess_run, while bypassing download/get_data/cache paths.
    batches, labels, session_ids, run_ids, indices = [], [], [], [], []
    names = None
    for session, raws in sessions:
        for run_id, raw in enumerate(raws):
            signals, run_labels, channel_names = preprocess(raw, EVENTS, config)
            if names is None:
                names = channel_names
            elif names != channel_names:
                raise ValueError("EEG channel order changed")
            batches.append(signals)
            labels.extend(run_labels)
            session_ids.extend([session] * len(run_labels))
            run_ids.extend([str(run_id)] * len(run_labels))
            indices.extend(range(len(run_labels)))
    if names is None:
        raise ValueError("no BCI runs")
    return {"signals": np.concatenate(batches), "labels": np.asarray(labels), "sessions": np.asarray(session_ids),
            "runs": np.asarray(run_ids), "trial_indices": np.asarray(indices, dtype=np.int64), "channel_names": np.asarray(names)}
