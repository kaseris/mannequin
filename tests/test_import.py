from unittest import TestCase


def test_mannequin_import():
    def _import():
        try:
            import mannequin
            return True
        except ImportError:
            return False

    assert _import() is True


def test_fileio_import():
    def _import():
        try:
            import mannequin.fileio
            return True
        except ImportError:
            return False

    assert _import() is True


def test_detection_import():
    def _import():
        try:
            import mannequin.detection
            return True
        except ImportError:
            return False

    assert _import() is True


def test_lerp_import():
    def _import():
        try:
            import mannequin.lerp
            return True
        except ImportError:
            return False

    assert _import() is True


def test_primitives_import():
    def _import():
        try:
            import mannequin.primitives
            return True
        except ImportError:
            return False

    assert _import() is True


def test_retrieval3d_import():
    def _import():
        try:
            import mannequin.retrieval3d
            return True
        except ImportError:
            return False

    assert _import() is True
