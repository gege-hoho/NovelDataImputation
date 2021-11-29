class Category:
    __slots__ = 'name', 'parent_categories', 'sub_categories', 'synonym', 'tokens'

    def __init__(self, category_name, synonym=""):
        self.name = category_name
        self.synonym = synonym
        self.parent_categories = []
        self.sub_categories = []
        self.tokens = []

    def add_parent(self, p):
        if p not in self.parent_categories:
            self.parent_categories.append(p)
        if self not in p.sub_categories:
            p.sub_categories.append(self)

    def __repr__(self):
        return self.name


def read_categories(path):
    f = open(path, 'r')
    cur_main_categories = []
    categories = {}
    i = 0
    for line in f:
        line = line.strip()
        if line.startswith('#'):
            continue
        if line.startswith('en:'):
            name = line.lstrip('en:').lower()
            names = name.split(',', 1)
            name = names[0]
            synonym = ""
            if len(names) > 1:
                synonym = names[1]
            c = Category(name, synonym)
            for parent in cur_main_categories:
                c.add_parent(parent)
            categories[name] = c

        if line.startswith('<en:'):
            main_category = line.lstrip('<en:').lower()
            if main_category not in categories:
                i += 1
                categories[main_category] = Category(main_category)
            cur_main_categories.append(categories[main_category])
        if line == "":
            cur_main_categories = []
    print(i)
    return categories