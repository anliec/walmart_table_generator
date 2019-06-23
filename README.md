# walmart_table_generator
A simple tool to convert walmart order text into a table and compute the share of every person involved

## Requirement

- Python 3
- Pandas

Tested under Ubuntu 19.04 with Python 3.7.3

## Usage

Copy the text from the confirmation email or your walmart acount and paste it into a text file. 

It should give you a text looking like that:

```
Substituted

    Bigelow Plantation Mint Classic Tea Bags - 20 CT20.0 CT
    1 × $2.48
    $2.48
    Substitute for Bigelow Green Tea with Mint 0.91 oz. Box
    $0.00
    [...]

Fulfilled
Weight Adjusted

    Granny Smith Apples, each
    3.19 lb × $1.97 / lb
    $6.28
    Substitute for Granny Smith Apples, each
    $0.00
    [...]

Other Items

    93% Lean/7% Fat, Lean Ground Beef, 4.5 lb
    1 × $17.94
    $17.94
    [...]
    
Out of Stock

    Eggplant
    0 @ $1.28 / lb
    $0.00
    [...]
    
Subtotal	$X
Delivery fee	$X
Total tax	$X
Order total	$X
```

This file can then be used as input to the script as:
```
python3 walmartMailTocsv.py -i <path-to-walmart-text-file> -o <path-to-output-table-csv> -p <list-of-persones-to-includes>
```
for example if you want to run the example provided in this repo:
```
python3 walmartMailTocsv.py -i example.txt -o example.csv -p me you someone him her
```
