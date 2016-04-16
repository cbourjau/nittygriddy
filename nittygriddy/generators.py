def make_chain():
    incollection = """
    adsf
    asdf
    asdfadsf
    """
    with open('run.C', 'r') as template:
        with open('test.txt', 'w') as output:
            for line in template.readlines():
                if "replace-token incollection" in line:
                    output.write(incollection)
                else:
                    output.write(line)


def make_local_file_list():
    """
    Generate a file with the full path to the desired local files
    """
    pass

