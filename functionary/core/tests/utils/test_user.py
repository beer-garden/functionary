from core.utils.user import normalize_dn


def test_normalize_removes_spaces():
    """Spaces between RDN pairs should be removed during DN normalization"""
    valid_dn = "CN=Test User,OU=Organization,C=US"
    dn_with_space = "CN=Test User,  OU=Organization, C=US"
    dn_with_one_space = "CN=Test User,OU=Organization, C=US"

    normal = normalize_dn(dn_with_space)
    assert normal == valid_dn

    normal = normalize_dn(dn_with_one_space)
    assert normal == valid_dn


def test_normalize_capitalizes_rdn_keys():
    """RDN names should be capitalized during DN normalization"""
    valid_dn = "CN=Test User,OU=Organization,C=US"
    dn_with_lower = "cn=Test User,ou=Organization,c=US"
    dn_with_some_lower = "Cn=Test User,OU=Organization, c=US"

    normal = normalize_dn(dn_with_lower)
    assert normal == valid_dn

    normal = normalize_dn(dn_with_some_lower)
    assert normal == valid_dn


def test_normalize_leaves_rdn_values_alone():
    """RDN values are left as is during DN normalization."""
    valid_dn = r"CN=Test User\ ,OU=organiZation\,,C=Us"
    dn_with_lower = r"cn=Test User\ ,ou=organiZation\,,c=Us"
    dn_with_some_lower = r"Cn=Test User\ ,OU=organiZation\,, c=Us"

    normal = normalize_dn(dn_with_lower)
    assert normal == valid_dn

    normal = normalize_dn(dn_with_some_lower)
    assert normal == valid_dn
