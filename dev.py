from dirtree import Directory

test_directory = Directory.init_from_yaml("templates.yaml", "test")

print(test_directory.tree())
test_directory.export_tree()
