#expand_bom.py
#Copyright 2018 Samuel B. Powell, samuel.powell@uq.edu.au

"""
@package
Create a csv or html BoM for netlists with "plural" names, as per expand_netlist.py.
The output format is selected from the file ending.

Command line:
python "pathToFile/expand_bom.py" "%I" "%O.html"
python "pathToFile/expand_bom.py" "%I" "%O.csv"
"""

from __future__ import print_function
#get the monkey-patched kicad_netlist_reader
from expand_netlist import kicad_netlist_reader, clean_name, expand_name, parse_letter_count
import sys, re

kicad_netlist_reader.excluded_values += ['MountingHole.*','TestPoint.*']

#additional fields:
#the defaults are 'Ref','Count','Value','Library','Part','Footprint','Description'
bom_extra_fields = ['Tolerance','Voltage','Note','Vendor','Part #','Purchased']

_ref_re = re.compile(r'([0-9]+)|([A-Za-z]+|[^A-Za-z0-9]+)')
def sort_key(name):
    parts = _ref_re.findall(name)
    return tuple(int(a) if a else b for a,b in parts)


#the default getInterestingComponents is mostly fine
# but the regex it uses to sort by ref fails on more complex refs
def getInterestingComponents(netlist):
    try:
        #we'll try the vanilla version first
        #esp because it does some stuff setting up regexes
        ret = netlist.getInterestingComponents()
    except:
        #but if it fails, we'll replicate it here
        ret = []
        for c in netlist.components:
            ex = False
            for refs in netlist.excluded_references:
                if refs.match(c.getRef()):
                    ex = True
                    break
            if not ex:
                for vals in netlist.excluded_values:
                    if vals.match(c.getValue()):
                        ex = True
                        break
            if not ex:
                for mods in netlist.excluded_footprints:
                    if mods.match(c.getFootprint()):
                        ex = True
                        break
            if not ex:
                ret.append(c)
        ret.sort(key = lambda g: sort_key(g.getRef()))
    return ret

#same deal with component grouping, only there's no reason to call the original
def groupComponents(components, eq=None):
    if eq is None:
        eq = lambda a,b: a == b
    
    groups = []
    for c in components:
        grouped = False
        #which group does this component belong to?
        for g in groups:
            if eq(g[0], c):
                g.append(c)
                grouped = True
                break
        #if we didn't find a group, make one
        if not grouped:
            groups.append([c])
    #sort within each group
    for g in groups:
        g.sort(key = lambda g: sort_key(g.getRef()))
    #sort groups by first item
    groups.sort(key = lambda g: sort_key(g[0].getRef()))
    return groups


def comp_eq(a, b):
    """compare more fields between components"""
    return  a.getValue() == b.getValue() \
        and a.getPartName() == b.getPartName() \
        and a.getFootprint() == b.getFootprint() \
        and a.getField("Tolerance") == b.getField("Tolerance") \
        and a.getField("Voltage") == b.getField("Voltage")


fields = ['Ref','Count','Value','Library','Part','Footprint','Description']
fields += bom_extra_fields

html_template = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        <title>KiCad BOM</title>
    </head>
    <body>
    <h1>{source:}</h1>
    <p>{date:}</p>
    <p>{tool:}</p>
    <p><b> Component Count:</b>{compcount:}</p>
    <table>
    {table:}
    </table>
    </body>
</html>
    """
html_row = "\n<tr>" + "<td>{}</td>"*len(fields) + "</tr>"
html_header = html_row.replace('td','th')

csv_template = """"Source","{source:}"
"Date","{date:}"
"Tool","{tool:}"
"Component count","{compcount:}"
{table:}
"""
csv_row = '\n' + ','.join(['"{}"']*len(fields))
csv_header = csv_row

def make_bom(netlist,template,header,row):
    comps = getInterestingComponents(netlist)
    groups = groupComponents(comps, comp_eq)
    total_count = 0
    
    table = header.format(*fields)
    for g in groups:
        refs = ''
        count = 0
        for comp in g:
            if refs:
                refs += ', '
            refs += clean_name(comp.getRef())
            count += len(expand_name(comp.getRef()))
        total_count += count
        c = g[0]
        extras = [c.getField(f) for f in bom_extra_fields]
        table += row.format(refs, count, c.getValue(), c.getLibName(), c.getPartName(),
                            c.getFootprint(),c.getDescription(), *extras)
    bom = template.format(source=net.getSource(),
                   date=net.getDate(), tool=net.getTool(),
                   compcount=total_count, table=table)
    return bom

if __name__ == '__main__':
    with open(sys.argv[2],'w') as f:
        if sys.argv[2].endswith(('htm','html')):
            template,header,row = html_template,html_header,html_row
        else:
            template,header,row = csv_template,csv_header,csv_row
        net = kicad_netlist_reader.netlist(sys.argv[1])
        bom = make_bom(net,template,header,row)
        print(bom,file=f)
