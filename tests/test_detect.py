"""Unit tests for GPU detection via PCI sysfs."""

from unittest.mock import AsyncMock, patch

import pytest

from deplodock.detect import _parse_sysfs_output, detect_local_gpus, detect_remote_gpus

# ── _parse_sysfs_output ────────────────────────────────────────────


def test_detect_local_gpus_nvidia():
    """Parse sysfs output with two identical NVIDIA GPUs."""
    output = "0x10de 0x2b85\n0x10de 0x2b85\n0x8086 0x1234\n"
    name, count = _parse_sysfs_output(output)
    assert name == "NVIDIA GeForce RTX 5090"
    assert count == 2


def test_detect_local_gpus_mixed_error():
    """Different GPU types raise RuntimeError."""
    output = "0x10de 0x2b85\n0x10de 0x2684\n"
    with pytest.raises(RuntimeError, match="Mixed GPU types"):
        _parse_sysfs_output(output)


def test_detect_local_gpus_no_gpus():
    """No recognized GPUs raise RuntimeError."""
    output = "0x8086 0x1234\n0x8086 0x5678\n"
    with pytest.raises(RuntimeError, match="No supported GPUs"):
        _parse_sysfs_output(output)


def test_detect_local_gpus_amd():
    """Parse sysfs output with AMD GPU."""
    output = "0x1002 0x75b0\n"
    name, count = _parse_sysfs_output(output)
    assert name == "AMD Instinct MI350X"
    assert count == 1


def test_detect_local_gpus_empty():
    """Empty output raises RuntimeError."""
    with pytest.raises(RuntimeError, match="No supported GPUs"):
        _parse_sysfs_output("")


# ── detect_local_gpus ──────────────────────────────────────────────


def test_detect_local_gpus_subprocess():
    """detect_local_gpus calls bash and parses output."""
    sysfs_output = "0x10de 0x2684\n" * 4
    mock_result = type("Result", (), {"returncode": 0, "stdout": sysfs_output, "stderr": ""})()
    with patch("subprocess.run", return_value=mock_result):
        name, count = detect_local_gpus()
        assert name == "NVIDIA GeForce RTX 4090"
        assert count == 4


def test_detect_local_gpus_nvidia_smi_fallback():
    """sysfs without supported GPUs (e.g. WSL2) falls back to nvidia-smi."""
    sysfs_result = type("Result", (), {"returncode": 0, "stdout": "0x1414 0x008e\n", "stderr": ""})()
    smi_result = type("Result", (), {"returncode": 0, "stdout": "NVIDIA GeForce RTX 5090\n", "stderr": ""})()

    def fake_run(cmd, *args, **kwargs):
        return smi_result if cmd[0] == "nvidia-smi" else sysfs_result

    with patch("subprocess.run", side_effect=fake_run):
        name, count = detect_local_gpus()
        assert name == "NVIDIA GeForce RTX 5090"
        assert count == 1


def test_detect_local_gpus_nvidia_smi_mixed_error():
    """nvidia-smi fallback raises on mixed GPU types."""
    sysfs_result = type("Result", (), {"returncode": 0, "stdout": "0x1414 0x008e\n", "stderr": ""})()
    smi_result = type(
        "Result",
        (),
        {"returncode": 0, "stdout": "NVIDIA GeForce RTX 5090\nNVIDIA GeForce RTX 4090\n", "stderr": ""},
    )()

    def fake_run(cmd, *args, **kwargs):
        return smi_result if cmd[0] == "nvidia-smi" else sysfs_result

    with patch("subprocess.run", side_effect=fake_run):
        with pytest.raises(RuntimeError, match="Mixed GPU types"):
            detect_local_gpus()


# ── detect_remote_gpus ─────────────────────────────────────────────


async def test_detect_remote_gpus():
    """detect_remote_gpus runs SSH and parses output."""
    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"0x10de 0x2330\n0x10de 0x2330\n", b"")
    mock_proc.returncode = 0

    with patch("deplodock.detect.asyncio.create_subprocess_exec", return_value=mock_proc):
        name, count = await detect_remote_gpus("user@host", "~/.ssh/id_ed25519", 22)
        assert name == "NVIDIA H100 80GB"
        assert count == 2
