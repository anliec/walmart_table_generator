#!/usr/bin/python3
import argparse
import os
import pandas as pd
import string

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input',
                    required=True,
                    type=str,
                    dest="input")
parser.add_argument('-o', '--output',
                    required=True,
                    type=str,
                    dest="out")
parser.add_argument('-p', '--involved-people',
                    required=False,
                    type=str,
                    nargs='+',
                    default=['Pierrick', 'Nicolas L.', 'Emma', 'Eymar', 'Tanguy', 'Nicolas S.'],
                    dest="persons")
args = parser.parse_args()

table = []
i = 0
section = "order"
state = "name"
name = ""
price_detail = ""
price = ""
with open(args.input, 'r') as f:
    subtotal = None
    delivery = None
    taxes = None
    total = None
    for line in f:
        line = line.replace("\t", "").replace("    ", "").replace("\n", "")
        if line == "":
            continue
        elif line == "Item details":
            continue
        elif line == "Substituted" or line == "Weight Adjusted":
            section = "sub"
        elif line == "Other Items" or line == "Fulfilled":
            section = "order"
        elif line == "Out of Stock":
            section = "out of stock"
        elif line[:8] == "Subtotal":
            section = "footer"
            subtotal = float(line.split('$')[-1])
        elif line[:12] == "Delivery fee":
            section = "footer"
            delivery = float(line.split('$')[-1])
        elif line[:9] == "Total tax":
            section = "footer"
            taxes = float(line.split('$')[-1])
        elif line[:11] == "Order total":
            section = "footer"
            total = float(line.split('$')[-1])
        elif section == "order" or section == "out of stock":
            if state == "name":
                name = line
                state = "detail"
            elif state == "detail":
                price_detail = line
                state = "price"
            else:
                price = line.replace('$', "")
                state = "name"
                table.append([name, price_detail, price])
        elif section == "sub":
            if state == "name":
                name = line
                if line != "$0.00":
                    state = "detail"
            elif state == "detail":
                price_detail = line.replace("Lower price!", "")
                state = "price"
            elif state == "price":
                price = line.replace('$', "")
                state = "sub"
            elif state == "sub":
                name += " " + line
                state = "useless"
            else:
                if '×' in line or '@' in line:
                    state = "useless"
                else:
                    state = "name"
                    table.append([name, price_detail, price])


d = pd.DataFrame(table, columns=["Product", "quantity x price", "total price"])
# add persons columns
for p in args.persons:
    d["{} share".format(p)] = pd.Series(data=[0] * len(d), index=d.index)
first_col = string.ascii_lowercase[3]
last_col = string.ascii_lowercase[3 + len(args.persons) - 1]
for i, p in enumerate(args.persons):
    in_col = 3 + i
    in_col_name = string.ascii_lowercase[in_col]
    price_fomula = []
    for j in range(2, len(d) + 2):
        price_fomula.append("=IF(SUM(${1}${0}:${2}${0}) = 0, 0, $C${0} * ${3}${0} / SUM(${1}${0}:${2}${0})"
                            .format(j, first_col, last_col, in_col_name))
    d["{} cost".format(p)] = pd.Series(data=price_fomula, index=d.index)

# add footer (totals)
per_person_total = [""] * (3 + len(args.persons) - 1) + ["Total"]
for i in range(len(args.persons)):
    col = string.ascii_lowercase[3 + len(args.persons) + i]
    per_person_total.append("=SUM(${0}$2:${0}${1})".format(col, len(d) + 1))

# sum of delivery and taxes
shared_price = "(${0}${1} + ${0}${2})".format('B', 1 + len(d) + 4, 1 + len(d) + 5)

per_person_total_plus_shares = [""] * (3 + len(args.persons) - 1) + ["Total TTC + delivery"]
first_col = string.ascii_lowercase[3 + len(args.persons)]
last_col = string.ascii_lowercase[3 + 2 * len(args.persons) - 1]
previous_line = 1 + len(d) + 1
for i in range(len(args.persons)):
    col = string.ascii_lowercase[3 + len(args.persons) + i]
    per_person_total_plus_shares.append("=${0}${1} + {2} / SUM(${3}${1}:${4}${1}) * ${0}${1}"
                                        .format(col, previous_line, shared_price, first_col, last_col))

other_info = list()
other_info.append(["Subtotal", subtotal])
other_info.append(["Delivery", delivery])
other_info.append(["Taxes", taxes])
other_info.append(["Paid", total])
other_info.append([])
other_info.append(["Current Total", "=SUM(${1}${0}:${2}${0})".format(previous_line + 1, first_col, last_col)])

for line in other_info:
    line += [""] * (len(d.columns) - len(line))

footer = pd.DataFrame([per_person_total, per_person_total_plus_shares] + other_info, columns=d.columns)

d = d.append(footer)

if os.path.splitext(args.out)[-1] == ".xlsx":
    d.to_excel(args.out, index=False, engine='xlsxwriter')
else:
    if os.path.splitext(args.out)[-1] != ".csv":
        print("Unknown file type {}, default to csv format".format(os.path.splitext(args.out)))
    d.to_csv(args.out, index=False)