# type: ignore

def test_package_import():
    import botcity.maestro as maestro
    assert maestro.__file__ != ""
