"""
Timezone conversion helper - stub for legacy script compatibility
"""

def convertFromIANATimezone(tz_string):
    """
    Convert IANA timezone to Windows format.
    For now, just return the input as-is since we're not using it in the new version.
    """
    if not tz_string:
        return ""
    return str(tz_string)

