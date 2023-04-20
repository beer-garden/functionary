from ldap import DECODING_ERROR
from ldap.dn import dn2str, str2dn


def normalize_dn(dn: str | None) -> str:
    """Normalizes a given DN to consistent capitalization and spacing.

    A DN usually has the format of 'CN=<first last>,OU=...,C=<country> where there
    are any number of these key/value pairs. This function will normalize the keys
    to be upper case and remove extraneous spaces after any ',' before another key.

    Args:
        dn: The DN to normalize

    Returns:
        The normalized DN as a string or an empty string

    Raises:
        ValueError for a malformed DN
    """
    try:
        valid_dn = str2dn(dn)
        normal_dn = [
            [(atype.upper(), avalue, dummy) for atype, avalue, dummy in rdn]
            for rdn in valid_dn
        ]

        return dn2str(normal_dn)
    except DECODING_ERROR as de:
        raise ValueError("Error decoding DN") from de
