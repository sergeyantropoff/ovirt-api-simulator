"""oVirt / RHV Engine API simulator domain package."""

__all__ = ["mount_ovirt_routes"]


def mount_ovirt_routes(*args, **kwargs):  # lazy re-export
    from app.ovirt.mount import mount_ovirt_routes as _mount

    return _mount(*args, **kwargs)
