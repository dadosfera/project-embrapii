from sqlglot import exp

class TableExtractor:

    def extract(self, tree: exp.Expression) -> list[str]:
        tables = set()

        for table in tree.find_all(exp.Table):
            tables.add(table.name)

        return sorted(tables)