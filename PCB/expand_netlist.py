# expand_netlist.py
# Copyright 2018 Samuel B. Powell, samuel.powell@uq.edu.au

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
@package
Expand a netlist with "plural" names into a KiCad Pcbnew netlist. This
replicates any components, pins, or nets with plural names as described below.
It cannot handle hierarchical sheets yet.

Command line:
python "pathToFile/expand_netlist.py" "%I" "%O.net" ["%O.xml"]

If the optional last argument is provided, this script also outputs the xml
netlist with names expanded, for use in BOM scripts or otherwise.

Components references, pin names, and net names (labels) are expanded using the
following operators:
  
  Lists are separated by commas: "A,B,C" -> "A", "B", "C"

  Ranges are written as either "start:stop", or "start:stop:step"
    start and stop must be non-negative integers or uppercase letters.
    step must be a positive integer.
    start and stop will both be included in the range unless you do something
      silly with step.
    stop may be less than start, in which case the range will count down. A
      negative step need not be specified.
    Valid letters are in "ABCDEFGHJKLMNPRTUVWY". IOQSXZ are excluded.
    Examples:
      "1:3" -> "1", "2", "3"        "3:1" -> "3", "2", "1"
      "0:10:5" -> "0","5","10"      "A:D" -> "A", "B", "C", "D"
      "A:D:2" -> "A", "C" (this is an example of being silly with step)

  The vertical bar "|" acts on lists and/or ranges, pairing items together.
    "A,B|1:3" -> "A1", "A2", "A3", "B1", "B2", "B3"

  Brackets "[]" replicate the surrounding text for each item within:
    "A[1,2,3]B" -> "A1B", "A2B", "A3B"
    If multiple replications occur in the same name it behaves like "|":
    "A[1,2].B[3,4]" -> "A1.B3", "A1.B4", "A2.B3", "A2.B4"
  
  Braces "{}" replicate text similarly to "[]" but discard the items within:
    "A{1,2,3}B" -> "AB", "AB", "AB"
    This is useful for wire labels when the cardinality of the wire name
    and what it's connecting to don't match.
    For example, an LED matrix has diodes D[1:5][A:F] with anodes connected to
    nets P[1:5] and cathodes connected to nets N[A:F]. By labeling the anode
    wire with P[1:5]{A:F} and cathode wire with N{1:5}[A:F] the appropriate
    connections can be made for each LED.

  A backtick "`" indicates that all following text should be discarded:
    "A[1:5]`1" -> "A1", "A2", ...
    This is to keep KiCad's annotation checker happy on netlist export.
    I.e. KiCad will not recognize "A[1:5]" as a valid reference before running this script,
     but it will accept "A[1:5]`1".
  

When expanding nets, there are two valid cases for how they are connected:
1) If the net name or any of the nodes the net connects to are singular,
   then all of the nodes are shorted together.
   E.g. Component "U[0:7]" pin "VCC" ("U[0:7].VCC") is connected to "3V3" by an unlabeled wire.
   Each of "U0.VCC" through "U7.VCC" will be shorted to "3V3".
2) If the net name and each node it connects to expand to name lists with the same
   cardinality, then a net is created connecting each corresponding node.
   E.g. Component "U1.OUT[0:7]" is connected to "D[15:8].A" by an unlabeled wire.
   8 nets are created connecting "U1.OUT0" to "D15.A", "U1.OUT1" to "D14.A", ...
Any other situations are treated as an error.
"""

from __future__ import print_function, division

import kicad_netlist_reader
import re
import sys

#monkey patch kicad_netlist_reader
def xml_copy(self,deep=True):
    """Copy and xmlElement, do not copy children unless deep is True"""
    other = kicad_netlist_reader.xmlElement(self.name,self.parent)
    other.attributes = self.attributes.copy()
    other.chars = self.chars
    if deep:
        for c in self.children:
            c = c.copy(True)
            c.parent = other
            other.children.append(c)
    else:
        other.children = self.children.copy()
    return other

def xml_formatNET(self,nestLevel=0):
    """Return xmlElement formatted as KiCad net
    nestLevel -- increases by one for each level of nesting.
    """
    s = ""
    
    indent = ""
    for i in range(nestLevel):
        indent += "  "
    
    s += indent + "(" + self.name
    for a in self.attributes:
        s += " (" + a
        val = self.attributes[a]
        if not val:
            s += " \"\")"
        elif re.search(r'[()\s]',val):
            s += " \"" + val + "\")"
        else:
            s += " " + val + ")"
    
    if self.chars:
        if re.search(r'[()\s]',self.chars):
            s += " \"" + self.chars + "\""
        else:
            s += " " + self.chars
    
    for c in self.children:
        s += "\n" + c.formatNET(nestLevel+1)
    
    s += ")"
    return s

def net_formatNET(self):
    """Return the netlist formatted as a KiCad .net"""
    return self.tree.formatNET()

kicad_netlist_reader.xmlElement.copy = xml_copy
kicad_netlist_reader.xmlElement.formatNET = xml_formatNET
kicad_netlist_reader.netlist.formatNET = net_formatNET

def outer_join(lists, delim='', prefix='',suffix=''):
    """join a list of lists of strings in an outer-product fashion"""
    strings = []
    if len(lists) > 1:
        for s in lists[0]:
            strings.extend(outer_join(lists[1:], delim, prefix+s+delim, suffix))
    else:
        for s in lists[0]:
            strings.append(prefix + s + suffix)
    return strings

_letters = 'ABCDEFGHJKLMNPRTUVWY'
def parse_letter_count(lc_str):
    """parse a number in the letter counting system
    Valid letters are in "ABCDEFGHJKLMNPRTUVWY". IOQSXZ are excluded.
    """
    #the A, ..., Y, AA ... counting system is weird
    #in multi-digit numbers, all but the last digit has value +1 (AA = 10, not 00)
    def get_letter_val(c,s):
        i = _letters.find(c)
        if i < 0: raise RuntimeError('invalid character in letter-count string: "'+c+'" in "'+lc_str+'"')
        return i

    if len(lc_str) == 1:
        val = get_letter_val(lc_str, lc_str)
    else:
        val = 0
        for c in lc_str[:-1]:
            val += 1 + get_letter_val(c, lc_str)
            val *= 20
        val += get_letter_val(lc_str[-1], lc_str)
    return val

def letter_count(val):
    """convert a non-negative int to a letter count"""
    #the first digit is base 20
    val += 1 #bcs the counting system is a bit strange
    count = ''
    while val > 0:
        val -= 1
        count = _letters[val%20] + count
        val = val//20
    return count

def expand_range(start,stop,step=None):
    """expand a range into a list of strings
    start and stop must non-negative integers or uppercase letters.
    stop may be less than start, in which the range will count down.
    step must be a positive (non-zero) integer, even if stop is less than start.
    start and stop will both be included unless you do something silly with step.
    valid letters are in "ABCDEFGHJKLMNPRTUVWY". IOQSXZ are excluded.
    """
    #assumes correct syntax
    if start[0] in _letters:
        lc = True
        start = parse_letter_count(start)
        stop = parse_letter_count(stop)
    else:
        lc = False
        start = int(start)
        stop = int(stop)
    if step is None:
        step = 1
    else:
        step = int(step)
        if step <= 0:
            raise RuntimeError('step must be positive (non-zero) integer')
    if stop < start:
        stop -= 1 #to make bounds inclusive
        step = -step
    else:
        stop += 1 #to make bounds inclusive
    r = range(start,stop,step)
    if lc:
        return [letter_count(i) for i in r]
    else:
        return [str(i) for i in r]

def clean_name(name):
    i = name.find('`')
    if i >= 0: return name[:i]+name[i+2:]
    else: return name

def _pop_name_stack(stack,keep_all,name):
    tos = stack.pop()
    name_list = tos[0]
    prefix = name_list.pop()
    join_list = []
    opener = None
    for item in tos[1:]:
        #keep track of what type of group we're in
        if item in ('[','{'): opener = item

        if keep_all: #keep everything in the strings
            join_list.append(item)
        elif item not in ('[',']','|','{','}'): #don't add braces
                if opener != '{': #don't add text within {}
                    join_list.append(item)
                else:
                    join_list.append(['']*len(item))
        #check matching braces
        if item in (']','}'):
            if opener is None or opener + item in ('{]','[}'):
                raise RuntimeError('ERROR: mismatched braces {} {} in name {}.'.format(opener,item,name))
            opener = None
    name_list.extend(outer_join(join_list,'',prefix))
    return name_list

#re: match any of "[]{}|/:,"
_expand_tokens = re.compile(r'([\[\]{}|/:,])')
#match '$0' to '$9', but only if not preceeded '\', ignore '\\'
_sub_var = re.compile(r'\$([1-9])')
#match []{}|/ or $0 to $9 or anything else
_sub_tokens = re.compile(r'[\[\]{}|/]|(?:\$[1-9])|(?:[^\[\]{}|/\$]+)')

def expand_name(name):
    #discard all after `
    name = clean_name(name)
    #quick search before expensive parsing
    m = _expand_tokens.search(name)
    if m is None:
        return [name]
    #are there any substitutions?
    sub_idxs = list(map(int,_sub_var.findall(name)))
    do_subs = len(sub_idxs) > 0
    #first expand the list of names
    #split the name into tokens
    tokens = _expand_tokens.split(name)
    #the regex only matches the operators, so the split function will
    # make it so that the operators will be in the odd indices of tokens
    #tokens.extend([']','']) #simplifies the logic below
    stack = []
    name_list = [tokens[0]]

    i = 1
    while i < len(tokens):
        next_op,next_name = tokens[i:i+2]
        if next_op in '[{':
            #push current state onto stack
            stack.append([name_list,next_op])
            name_list = [next_name]
            i += 2
        elif next_op == ',':
            name_list.append(next_name)
            i += 2
        elif next_op == ':':
            start = name_list.pop()
            stop = next_name
            i += 2
            #look ahead to get step
            if i + 1 < len(tokens) and tokens[i] == ':':
                step = tokens[i+1]
                i += 2
            else:
                step = None
            name_list.extend(expand_range(start,stop,step))
        elif next_op in '|/':
            # | and / are shorthand for ][
            if not stack: #the stack was empty, fix it
                stack.append([]) #[''],'['])
                
            #put our stuff on the top of the stack
            stack[-1].extend([name_list,next_op])
            name_list = [next_name]
            i += 2
        elif next_op in ']}':
            if not stack: #the stack was empty, error
                raise RuntimeError('ERROR: Unmatched brace {} in name {}'.format(next_op,name))
            #put our stuff on the top of the stack
            stack[-1].extend([name_list,next_op,[next_name]])
            i += 2
            if i + 1 < len(tokens) and tokens[i] in '[{':
                next_op,next_name = tokens[i:i+2]
                #look ahead to see if we're doing more
                stack[-1].extend([next_op]) #previous name_list is already on stack
                name_list = [next_name]
                i += 2
            else:
                #no, go ahead and close this one out
                name_list = _pop_name_stack(stack,do_subs,name)
        else:
            #this shouldn't ever happen unless we made a mistake in the regex
            raise RuntimeError('ERROR: Unrecognized operator {} in name {}'.format(next_op,name))
    #is there anything left on the stack?
    while stack:
        #pretend we're ending with ']' until the stack is empty
        stack[-1].extend([name_list])
        name_list = _pop_name_stack(stack,do_subs,name)
    #do we need to do substitutions?
    if do_subs:
        new_name_list = []
        for name in name_list:
            tokens = _sub_tokens.findall(name)
            groups = []
            opener = None
            new_name = []
            for t in tokens:
                if t in '[{': #start a new group
                    opener = t
                    groups.append([])
                elif t in ']}':
                    opener = None
                elif t != '|':
                    if opener is not None:
                        groups[-1].append(t)
                    if opener != '{':
                        new_name.append(t)
            for i,n in enumerate(new_name):
                m = _sub_var.match(n)
                if m is not None:
                    new_name[i] = ''.join(groups[int(m.group(1))-1])
            new_name_list.append(''.join(new_name))
        name_list = new_name_list
    return name_list

class tstamper:
    def __init__(self,start,use_hex=True,used=set()):
        self.next = start
        self.use_hex = use_hex
        self.used = used
    
    def set_next(self,nxt):
        self.next = nxt

    def __call__(self):
        if self.use_hex:
            s = hex(self.next)[2:].upper()
        else:
            s = str(self.next)
        self.used.add(self.next)
        while self.next in self.used:
            self.next += 1
        return s

def transform(netlist):
    fail = False

    #scan for all the timestamps being used
    if netlist.components:
        tstamps = set()
        for comp in netlist.components:
            tstamps.add(int(comp.getTimestamp(),16))
    
    #make a timestamper -- increments tstamps, skips those already used
    ts = tstamper(0,used=tstamps)
    
    #we work with the xmlElement objects rather than the wrappers
    #we'll fix up the wrapper objects after
    
    #first deal with replicating components:
    if netlist.components:
        components = netlist.components[0].element.parent
        new_kids = []
        
        for child in components.children:
            ref = child.attributes['ref']
            refs = expand_name(ref)
            if len(refs) > 1:
                ts.set_next(int(child.getChild('tstamp').chars,16))
                for r in refs:
                    c = child.copy() #deep copy
                    c.setAttribute('ref',r)
                    c.getChild('tstamp').chars = ts()
                    new_kids.append(c)
            else: #not plural, don't change
                new_kids.append(child)
        components.children = new_kids
        netlist.components = [kicad_netlist_reader.comp(x) for x in new_kids]
    
    #now with pins in each libpart
    for libpart in netlist.libparts:
        pins = libpart.element.getChild('pins')
        #some parts have no pins:
        if pins is None: continue
        new_kids = []
        for pin in pins.children:
            num = pin.attributes['num']
            name = pin.attributes['name']
            
            nums = expand_name(num)
            names = expand_name(name)

            if len(nums) > 1:
                if len(names) > 1:  # Case 1: both are plural
                    if len(nums) != len(names): #uh oh!
                        print("Error: Mismatched pin nums and names in libpart:",libpart.getLibName(), "/", libpart.getPartName(), file=sys.stderr)
                        fail = True
                        continue #skip to next pin
                    for num,name in zip(nums,names):
                        p = pin.copy() #deep copy
                        p.setAttribute('num',num)
                        p.setAttribute('name',name)
                        new_kids.append(p)
                else: #case 2: plural nums, single name
                    for num in nums:
                        p = pin.copy()
                        p.setAttribute('num',num)
                        new_kids.append(p)
            else: #single num
                if len(names) > 1:  # case 3: single num, plural name
                    #does this case even make sense?
                    for name in names:
                        p = pin.copy()
                        p.setAttribute('name',name)
                        new_kids.append(p)
                else:  # case 4: single num, single name
                    new_kids.append(pin)
        pins.children = new_kids
    #now to deal with nets
    #this is slightly more complicated because the labels might not be identical
    #so we could have to merge multiple nets into one
    if netlist.nets:
        nets = netlist.nets[0].parent
        new_names = []
        new_nets = {}
        next_code = tstamper(1,False)
        for net in nets.children:
            #each net has 2 attributes: code & name
            # and nodes as children, each with 'ref' and 'pin' attributes
            #If the net was labeled, it's name is that label
            #if the net is automatically named, it name will be taken from
            #one of the nodes it's connected to: "Net-({ref}-Pad{pin})"
            
            #there are 2 valid cases here:
            # 1) if any of the names are singular, we short everything together in one net
            # 2) if all of the names are plural to the same degree, we make new nets for each

            #this is a two-pass algorithm
            #first we expand everything
            name = net.attributes['name']
            names = expand_name(name)
            short = (len(names) == 1)
            len_mismatch = None
            node_refs_pins = []
            for node in net.children:
                ref,pin = node.attributes['ref'], node.attributes['pin']
                refs = expand_name(ref)
                pins = expand_name(pin)
                nrp = [(node,r,p) for r in refs for p in pins]
                node_refs_pins.append(nrp)
                if len(nrp) == 1:
                    short = True
                elif len(nrp) != len(names):
                    len_mismatch = ref,pin
                    #we check for the length mismatch here, but we can't call it an error
                    # yet because we don't know for sure if we're shorting everything
            #second pass, reconstruct net(s)
            if short:
                new_kids = []
                for nrps in node_refs_pins:
                    for node,ref,pin in nrps:
                        n = node.copy()
                        n.attributes['ref'] = ref
                        n.attributes['pin'] = pin
                        new_kids.append(n)
                net.children = new_kids
                net.attributes['code'] = next_code()
                new_nets[names[0]]= net
                new_names.append(names[0])
            else:
                #not shorting, everything should have the same length
                if len_mismatch is not None:
                    ref,pin = len_mismatch
                    print('Error: mismatch between net and node:',name,'!= (',ref,pin,')')
                    fail = True
                    continue #skip to next net
                #iterate through the net names and expanded nodes together
                for name, nrps in zip(names, zip(*node_refs_pins)):
                    if name in new_nets:
                        #we've already worked on a net with the same name, use it
                        new_net = new_nets[name]
                        new_kids = new_net.children
                    else:
                        #otherwise we make a new net
                        new_names.append(name) #to preserve order
                        new_net = net.copy()
                        new_kids = []
                        new_net.attributes['name'] = name
                        new_net.attributes['code'] = next_code()
                        new_net.children = new_kids
                        new_nets[name] = new_net
                    for node,ref,pin in nrps:
                        n = node.copy()
                        n.attributes['ref'] = ref
                        n.attributes['pin'] = pin
                        new_kids.append(n)
            #done with the net
        #done making new_nets
        nets.children = [new_nets[name] for name in new_names]

    if fail:
        sys.exit(1)

if __name__ == '__main__':

    #check usage:
    if len(sys.argv) < 3:
        print("Usage: ", __file__, "<generic_netlist.xml> <output.net> [<output.xml>]", file=sys.stderr)
        sys.exit(1)
    
    #load the netlist:
    net = kicad_netlist_reader.netlist(sys.argv[1])

    #open outputs
    try:
        f = open(sys.argv[2],'wb')
    except IOError:
        print("Can't open output file for writing: " + sys.argv[2],file=sys.stderr)
        sys.exit(1)

    f_xml = None
    if len(sys.argv) > 3:
        try:
            f_xml = open(sys.argv[3],'wb')
        except IOError:
            print("Can't open output file for writing: " + sys.argv[3],file=sys.stderr)
            sys.exit(1)

    #edit netlist in place
    transform(net)

    #save to file
    with f:
        f.write(net.formatNET().encode('utf8'))
        #print(net.formatNET().encode('utf8'),file=f)
    
    if f_xml is not None:
        with f_xml:
            f_xml.write(net.formatXML().encode('utf8'))
            #print(net.formatXML().encode('utf8'),file=f_xml)
    
    sys.exit(0)
