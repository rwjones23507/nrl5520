#!usr/bin/env python

"""
This script transforms mgen network data into a D3JS-readable json file.

The script opens an mgen log file, reads each line, validates the structure and content of RECV lines, validates
the structure of the source and destination node IP addresses, transforms the IP addresses to a new format, creates
json objects from the source and destination nodes that can be used to generate D3JS graphics, and writes the json
objects to a separate file.

At its core, the script performs a simple extract-transform-load (ETL) process:

    1. Source and destination IP addresses are extracted from each mgen line (after data has been validated).
    2. The IP addresses are transformed from an 'nnn.nnn.nnn.nnn' format to an 'mgen.nnn-nnn-nnn-nnn' format.
    3. The transformed IP addresses are loaded into a json file that can be used to render D3JS graphics.

Notional mgen RECV lines:

    22:55:07.470450 RECV proto>UDP flow>1 seq>0 src>127.0.0.1/5001 dst>127.0.0.2/5000 sent>22:55:07.470351 size>1024
    22:55:08.470981 RECV proto>UDP flow>1 seq>1 src>127.0.0.1/5001 dst>127.0.0.2/5000 sent>22:55:08.470860 size>1024
    22:55:10.471264 RECV proto>UDP flow>2 seq>0 src>127.0.0.1/5001 dst>127.0.0.3/5000 sent>22:55:10.471120 size>1024
    22:55:11.471280 RECV proto>UDP flow>3 seq>0 src>127.0.0.2/5001 dst>127.0.0.3/5000 sent>22:55:11.471140 size>1024
    22:55:13.471262 RECV proto>UDP flow>4 seq>0 src>127.0.0.2/5001 dst>127.0.0.1/5000 sent>22:55:13.471120 size>1024
    22:55:14.471251 RECV proto>UDP flow>5 seq>0 src>127.0.0.1/5001 dst>127.0.0.4/5000 sent>22:55:14.471128 size>1024

Notional output file:

    [
     {"name": "mgen.127-0-0-1", "size": 3, "imports": ["mgen.127-0-0-2", "mgen.127-0-0-3", "mgen.127-0-0-5"},
     {"name": "mgen.127-0-0-2", "size": 2, "imports": ["mgen.127-0-0-1", "mgen.127-0-0-3"},
     {"name": "mgen.127-0-0-3", "size": 0, "imports": []},
     {"name": "mgen.127-0-0-4", "size": 0, "imports": []},
    ]

The script contains a primary function and utility functions.

Primary function:

    convert_mgen_to_json: Read an mgen log file, convert each line to a json element, and write out to a json file.

Utility functions:

    rename_file: Re-name input file by changing extension to .json (in the absence of a user-specified output file).

    validate_recv_mgen_line: Check that source and destination fields exist in the expected places in mgen RECV line.

    validate_node_address: Check that the node address is a valid ip address.

    convert_node_address: Convert node IP address from 'nnn.nnn.nnn.nnn' format to 'mgen.nnn-nnn-nnn-nnn'.

Exceptions:

    FileNotFoundError if input_file cannot be found/opened
    ValueError if the input_file is empty
    UnicodeDecodeError if the input_file is not a text file (not developed yet)
    FileNotFoundError if the output_file cannot be opened
    IndexError if src> or dst> are not found in the expected locations
    ValueError if the src or dst node addresses are not valid IP addresses

title: mgen_2_d3js.py
version: 1.0
date: 29 June 2015
author: Rick Jones
"""

import argparse
import ipaddress
import json
import logging
import os


def rename_file(input_file):
    """
    Re-name input file by changing extension to .json (in the absence of a user-specified output file).

    :param: (str): The path and filename of the file to be renamed
    :returns: (str) output_file
    :raises: Nothing
    """

    output_file = input_file.rsplit(".", 1)[0] + ".json"
    return output_file


def validate_recv_mgen_line(mgen_line, count):
    """
    Check that source and destination fields exist in the expected places in mgen RECV line.

    :param: (str) mgen_line
    :param: (int) count (for identifying location of IndexError)
    :returns: False if src> or dst> are not found in the expected positions; nothing otherwise
    :raises: IndexError if src> and dst> are not found in the expected positions
    """

    try:
        if mgen_line[5][0:4] != 'src>':
            raise IndexError('In mgen_line', count, 'the src address is not in the expected position. Ignoring this '
                                                    'record.')
    except IndexError as errMsg:
        print(errMsg)
        logging.exception(errMsg)
        return False
    try:
        if mgen_line[6][0:4] != 'dst>':
            raise IndexError('In mgen_line', count, 'the dst address is not in the expected position. Ignoring this '
                                                    'record.')
    except IndexError as errMsg:
        print(errMsg)
        logging.exception(errMsg)
        return False


def validate_node_address(node_address, count):
    """
    Validate the node_address is a proper IP address

    :param: (str) node_address
    :param: (int) count (for identifying location of ValueError)
    :returns: False if node address is not a valid IP address; nothing otherwise
    :raises: ValueError if node_address is not a valid IP address
    """
    node_address = node_address.split("/")[0]
    try:
        ipaddress.ip_address(node_address)
    except ValueError as errMsg:
        print("In record", count, ", one of the node addresses", errMsg, ". Ignoring this record.")
        logging.exception(errMsg)
        return False


def convert_node_address(node_address):
    """
    Convert 'nnn.nnn.nnn.nnn' IP address format to 'mgen.nnn-nnn-nnn-nnn'.

    :param: (str) node IP address
    :returns: (str) node name in json format
    :raises: Nothing
    """
    node_name = node_address.split("/")[0]
    node_name = node_name.split(".")
    node_name = "mgen." + node_name[0] + "-" + node_name[1] + "-" + node_name[2] + "-" + node_name[3]
    return node_name


def convert_mgen_to_json(input_file, output_file=None):
    """
    Read an mgen log file, convert each line to a json element, and write out to a json file.

    :param: (str) input_file path and file name
    :param: (str) Optional output_file path and file name
    :returns: Nothing
    :raises: FileNotFoundError if input_file cannot be found/opened
    :raises: ValueError is input_file is empty
    :raises: UnicodeDecodeError is the input file is not a text file (not developed yet)
    :raises: FileNotFoundError is output_file cannot be found/opened
    """
    json_dicts = []
    count = 0  # Identifies location of errors

    if output_file is None:
        output_file = rename_file(input_file)

    try:
        with open(input_file, 'r') as f:
            try:
                if os.stat(input_file).st_size == 0:
                    raise ValueError("The input file seems to be empty.")
            except ValueError as errMsg:
                print(errMsg)
                logging.exception(errMsg)
            try:
                with open(output_file, 'a') as g:
                    try:
                        for mgen_line in f.readlines():
                            if mgen_line == "\n":
                                continue
                            else:
                                count += 1
                                mgen_line = mgen_line.split(" ")
                                if mgen_line[1] == 'RECV':
                                    # Validate mgen line contains a src> and dst> in expected locations, or else ignore
                                    # mgen_line
                                    if validate_recv_mgen_line(mgen_line, count) is False:
                                        continue
                                    # Validate source node address is an IP address or ignore mgen_line
                                    if validate_node_address(mgen_line[5][4:], count) is False:
                                        continue
                                    # Validate destination node address is an IP address or ignore mgen_line
                                    if validate_node_address(mgen_line[6][4:], count) is False:
                                            continue
                                    # Convert source node address to json format
                                    srcnode = convert_node_address(mgen_line[5][4:])
                                    # Convert destination node address to json format
                                    dstnode = convert_node_address(mgen_line[6][4:])
                                    # Create the first dict if the json_dicts list is empty
                                    if not json_dicts:
                                        size = 1
                                        json_dicts.append({"name": srcnode, "size": size, "imports": [dstnode]})
                                    # Append a new dict to the json_dicts list if the srcnode has not been processed yet
                                    elif srcnode not in [json_dict["name"] for json_dict in json_dicts]:
                                        size = 1
                                        json_dicts.append({"name": srcnode, "size": size, "imports": [dstnode]})
                                    # Append dstnodes to "imports" if the srcnode has already been processed
                                    elif srcnode in [json_dict["name"] for json_dict in json_dicts]:
                                        for json_dict in json_dicts:
                                            if json_dict["name"] == srcnode:
                                                if dstnode not in json_dict["imports"]:
                                                    json_dict["size"] += 1
                                                    json_dict["imports"].append(dstnode)
                                    # Create a dict with empty "imports" for dstnode that is not a srcnode
                                    if dstnode not in [json_dict["name"] for json_dict in json_dicts]:
                                        dstnodesize = 0
                                        json_dicts.append({"name": dstnode, "size": dstnodesize, "imports": []})
                        g.write(json.dumps(json_dicts))
                    except UnicodeDecodeError as errMsg:
                        print("UnicodeDecodeError: The input file is not a text file.")
                        logging.exception(errMsg)
            except IOError as errMsg:
                print("FileNotFoundError: Cannot find", output_file, "or write data. Check directory path/file name.")
                logging.exception(errMsg)
    except FileNotFoundError as errMsg:
        print("FileNotFoundError: Cannot find", input_file, "- Check directory path and file name.")
        logging.exception(errMsg)


def main():

    logging.basicConfig(filename='./data_test/d3js_error.log', format='%(asctime)s %(message)s')

    parser = argparse.ArgumentParser(description='Read and convert mgen files to D3JS-friendly json files.')

    parser.add_argument('infile', help='File to be read and processed.')
    parser.add_argument('--outfile', help='Path and name of output file.')

    args = parser.parse_args()

    convert_mgen_to_json(args.infile, args.outfile)


if __name__ == '__main__':
    main()


# TODO: Create unit tests
# Tighten up the architecture and code

# Test cases:
# 0: Good file
# 1: Bad path/filename for input file
# 2: Empty input file
# 3: Binary input file
# 4: Bad path for output file
# 5: 'src>' not in the correct places in the RECV line
# 6: 'dst>' are not in the correct places in the RECV line
# 7: IP address is not valid
