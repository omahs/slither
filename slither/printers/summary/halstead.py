"""
    Halstead complexity metrics
"""
import math
from slither.printers.abstract_printer import AbstractPrinter
from slither.slithir.variables.temporary import TemporaryVariable
from slither.utils.myprettytable import MyPrettyTable


# Converts a dict to a MyPrettyTable.  Dict keys are the contract names.
# @param headers str[] of column names starting with "Contract"
# @param body dict of contract names with a dict of the values
# @param totals bool optional add Totals row
# TODO: Move this to shared
def make_pretty_table(headers: list, body: dict, totals: bool = False) -> MyPrettyTable:
    table = MyPrettyTable(headers)
    for contract in body:
        row = [contract] + [body[contract][key] for key in headers[1:]]
        table.add_row(row)
    if totals:
        table.add_row(
            ["Total"] + [sum([body[contract][key] for contract in body]) for key in headers[1:]]
        )
    return table


# @param takes a list of contract objects
# @param returns a dict(k:contract names, v: dict of core metrics)
# {
#   "contract1_name": {
#       total_operators: int,
#       unique_operators: int,
#       total_operands: int,
#       unique_operands: int
#   },
#   "contract2_name": {
#       total_operators: int,
#       unique_operators: int,
#       total_operands: int,
#       unique_operands: int
#   },
# }
def compute_ops(contracts: list) -> dict:
    mapping = {}
    for contract in contracts:
        operators = []
        operands = []
        for func in contract.functions:
            for node in func.nodes:
                for operation in node.irs:
                    # use operation._expression._type to get the unique operator type
                    operator_type = operation._expression._type
                    operators.append(operator_type)

                    # use operation.used to get the operands of the operation ignoring the temporary variables
                    new_operands = [
                        op for op in operation.used if not isinstance(op, TemporaryVariable)
                    ]
                    operands.extend(new_operands)
        mapping[contract.name] = {
            "total_operators": len(operators),
            "unique_operators": len(set(operators)),
            "total_operands": len(operands),
            "unique_operands": len(set(operands)),
        }
    return mapping

def compute_core_metrics(contracts_ops: dict) -> dict:
    mapping = {}
    for contract in contracts_ops:
        total_operators = contracts_ops[contract]["total_operators"]
        unique_operators = contracts_ops[contract]["unique_operators"]
        total_operands = contracts_ops[contract]["total_operands"]
        unique_operands = contracts_ops[contract]["unique_operands"]
        n1 = unique_operators
        n2 = unique_operands
        N1 = total_operators
        N2 = total_operands
        n = n1 + n2
        N = N1 + N2
        V = N * math.log(n, 2)
        D = (n1 / 2) * (N2 / n2)
        E = D * V
        T = E / 18
        B = T / 3000
        mapping[contract] = {
            "n1": n1,
            "n2": n2,
            "N1": N1,
            "N2": N2,
            "n": n,
            "N": N,
            "V": V,
            "D": D,
            "E": E,
            "T": T,
            "B": B,
        }
    return mapping
class Halstead(AbstractPrinter):
    ARGUMENT = "halstead"
    HELP = "Computes the Halstead complexity metrics for each contract"

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#halstead"

    def output(self, _filename):
        contracts_ops = compute_ops(self.contracts)
        if len(self.contracts) == 0:
            return self.generate_output("No contract found")

        txt = "Halstead complexity metrics:\n"

        # Core metricts: contracts_ops and operands
        keys = [k for k in contracts_ops[self.contracts[0].name].keys()]
        table1 = make_pretty_table(["Contract", *keys], contracts_ops, True)
        # TODO: Any benefit to breaking it down further by func? or adding Totals?
        txt += "  total_operators: the total number of operators\n"
        txt += "  unique_operators: the number of distinct operators\n"
        txt += "  total_operands: the total number of operands\n"
        txt += "  unique_operands: the number of distinct operands\n" + str(table1) + "\n"
        core_metrics = compute_core_metrics(contracts_ops)
        import pdb; pdb.set_trace()

        res = self.generate_output(txt)
        res.add_pretty_table(table1, "Halstead core metrics")
        self.info(txt)

        return res
