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
                    default=['Pierrick', 'Nicolas L. & Emma', 'Eymar', 'Guillaume', 'Nicolas S.', 'Thomas', 'Louis',
                             'Marie', "Vincent"],
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
    tip = 0
    for line in f:
        line = line.replace("\t", "").replace("    ", "").replace("\n", "")
        line_formated = line.replace("-", " ").lower()
        # print("{}\t{}\t{}".format(line, section, state))
        if line == "":
            continue
        elif line == "Item details":
            continue
        elif line_formated[:11] == "substituted" or line_formated[:15] == "weight adjusted":
            section = "sub"
            state = "name"
        elif line_formated[:11] == "other items" or line_formated[:9] == "fulfilled" or \
                line_formated [:12] == "picked items":
            section = "order"
            state = "name"
        elif line_formated[:12] == "out of stock":
            section = "out of stock"
            state = "name"
        elif line_formated[:8] == "subtotal":
            section = "footer"
            subtotal = float(line.split('$')[-1])
        elif line[:12] == "Delivery fee":
            section = "footer"
            delivery = float(line.split('$')[-1])
        elif line[:10] == "Driver tip":
            section = "footer"
            tip = float(line.split('$')[-1])
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
                price_detail += line.replace("Lower price!", "")
                if '×' in line:
                    state = "price"
            else:
                if section == "out of stock":
                    price = "0"
                else:
                    price = line.replace('$', "")
                state = "name"
                table.append([name, price_detail, price])
                name = ""
                price_detail = ""
                price = ""
        elif section == "sub":
            if state == "name":
                name = line
                if line != "$0.00":
                    state = "detail"
            elif state[:6] == "detail":
                price_detail += line.replace("Lower price!", "")
                if '×' in line:
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
                    name = ""
                    price_detail = ""
                    price = ""


d = pd.DataFrame(table, columns=["Product", "quantity x price", "total price"])
# add per item shared price

first_col = string.ascii_lowercase[4 + len(args.persons)]
last_col = string.ascii_lowercase[4 + len(args.persons) * 2 - 1]
price_fomula = []
for i in range(2, len(d) + 2):
    price_fomula.append("=SUM(${1}${0}:${2}${0})"
                        .format(i, first_col, last_col))
d["shared cost"] = pd.Series(data=price_fomula, index=d.index)
# add persons columns
for p in args.persons:
    d["{} share".format(p)] = pd.Series(data=[0] * len(d), index=d.index)
first_col = string.ascii_lowercase[4]
last_col = string.ascii_lowercase[4 + len(args.persons) - 1]
for i, p in enumerate(args.persons):
    in_col = 4 + i
    in_col_name = string.ascii_lowercase[in_col]
    price_fomula = []
    for j in range(2, len(d) + 2):
        price_fomula.append("=IF(SUM(${1}${0}:${2}${0})=0;0;$C${0}*${3}${0}/SUM(${1}${0}:${2}${0})"
                            .format(j, first_col, last_col, in_col_name))
    d["{} cost".format(p)] = pd.Series(data=price_fomula, index=d.index)

# add footer (totals)
per_person_total = [""] * (4 + len(args.persons) - 1) + ["Total"]
for i in range(len(args.persons)):
    col = string.ascii_lowercase[4 + len(args.persons) + i]
    per_person_total.append("=SUM(${0}$2:${0}${1})".format(col, len(d) + 1))

# sum of delivery and taxes and tip
shared_price = "(${0}${1} + ${0}${2} + ${0}${3})".format('B', 1 + len(d) + 4, 1 + len(d) + 5, 1 + len(d) + 7)

per_person_total_plus_shares = [""] * (4 + len(args.persons) - 1) + ["Total TTC + delivery + tip"]
first_col = string.ascii_lowercase[4 + len(args.persons)]
last_col = string.ascii_lowercase[4 + 2 * len(args.persons) - 1]
previous_line = 1 + len(d) + 1
for i in range(len(args.persons)):
    col = string.ascii_lowercase[4 + len(args.persons) + i]
    per_person_total_plus_shares.append("=${0}${1} + {2} / SUM(${3}${1}:${4}${1}) * ${0}${1}"
                                        .format(col, previous_line, shared_price, first_col, last_col))

other_info = list()
other_info.append(["Subtotal", subtotal])
other_info.append(["Delivery", delivery])
other_info.append(["Taxes", taxes])
other_info.append(["Paid", total])
other_info.append(["Tip", tip])
other_info.append(["With tip", total + tip])
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
