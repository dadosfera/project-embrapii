# sql_analysis/pattern_extractor.py
from sqlglot import exp

from benchmark_generator.domain.models import QueryPattern

AGG_FUNCS = {
    "COUNT", "SUM", "AVG", "MIN", "MAX"
}

class QueryPatternExtractor:

    def extract(self, tree: exp.Expression) -> list[QueryPattern]:
        patterns: set[QueryPattern] = {"select"}

        if tree.find(exp.Where):
            patterns.add("filter")

        if tree.find(exp.Join):
            patterns.add("join")

        if tree.find(exp.Group):
            patterns.add("aggregation")

        if tree.find(exp.Order) or tree.find(exp.Limit):
            patterns.add("ordering")

        if tree.find(exp.Union) or tree.find(exp.Intersect) or tree.find(exp.Except):
            patterns.add("set")

        # subquery
        if any(
            isinstance(node, exp.Subquery)
            for node in tree.walk()
        ):
            patterns.add("subquery")

        # dialect-specific functions
        for func in tree.find_all(exp.Func):
            if func.name.upper() not in AGG_FUNCS:
                patterns.add("dialect_function")
                break

        return sorted(patterns)