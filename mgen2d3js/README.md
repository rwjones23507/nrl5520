#### I - General Guidance

##### Overview

The script opens an mgen log file, reads each line and filters on RECV lines, validates the presence and location of the source and destination node IP addresses, validates the structure and formatting of the IP addresses, transforms the IP addresses to a new format, creates json objects from the source and destination nodes that can be used to generate D3JS graphics, and writes the json objects to a separate file.

##### Specifics

Each RECV line has the source and destination node IP addresses extracted. The IP addresses are transformed from the standard `nnn.nnn.nnn.nnn` format to `mgen.nnn-nnn-nnn-nnn` to facilitate d3js rendering.

For each source node, a Python dictionary is created with three keys: name, size, and imports

* The `name` key is assigned the transformed source IP address as its value
* The `size` key is assigned the number of distinct destination nodes associated with the source node as its value
* The `imports` key is assigned a list as its value, containing the transformed IP addresses of all associated destination nodes

In the event that a destination node exists that does not also function as a source node, a dictionary is created with a `"size":0` and `"imports":[]`

All the dictionaries are combined into a `.json` file that can be rendered into a d2js graphic.

##### Notional Example

Notional mgen RECV lines such as the following:

```22:55:07.470450 RECV proto>UDP flow>1 seq>0 src>127.0.0.1/5001 dst>127.0.0.2/5000 sent>22:55:07.470351 size>1024```
```22:55:08.470981 RECV proto>UDP flow>1 seq>1 src>127.0.0.1/5001 dst>127.0.0.2/5000 sent>22:55:08.470860 size>1024```
```22:55:10.471264 RECV proto>UDP flow>2 seq>0 src>127.0.0.1/5001 dst>127.0.0.3/5000 sent>22:55:10.471120 size>1024```
```22:55:11.471280 RECV proto>UDP flow>3 seq>0 src>127.0.0.2/5001 dst>127.0.0.3/5000 sent>22:55:11.471140 size>1024```
```22:55:13.471262 RECV proto>UDP flow>4 seq>0 src>127.0.0.2/5001 dst>127.0.0.1/5000 sent>22:55:13.471120 size>1024```
```22:55:14.471251 RECV proto>UDP flow>5 seq>0 src>127.0.0.1/5001 dst>127.0.0.4/5000 sent>22:55:14.471128 size>1024```
 
Will produce a notional output file such as the following:

```
[
 {"name": "mgen.127-0-0-1", "size": 3, "imports": ["mgen.127-0-0-2", "mgen.127-0-0-3", "mgen.127-0-0-5"},
 {"name": "mgen.127-0-0-2", "size": 2, "imports": ["mgen.127-0-0-1", "mgen.127-0-0-3"},
 {"name": "mgen.127-0-0-3", "size": 0, "imports": []},
 {"name": "mgen.127-0-0-4", "size": 0, "imports": []},
]
```
 
#### II - Usage

`parsefile.py <infile>` `[output <outfile>]`<sup>1</sup>

<sup>1</sup>The default outfile is the path/filename of the input file, with the file extension changed to .json

Command Line Parameters and Options

| Parameter     | Description   |
| ------------- | ------------- |
| infile        | Specifies location and name of file to be processed.|
| [outfile <path/file> ]  | Specifies output file location and name. Default is input file location and name with the file extension changed to .json.|

#### III - Exception Handling

The following exceptions may be raised:

| Exception     | Condition    | Action   |
| ------------- | ------------ | -------- |
| FileNotFoundError | Input file cannot be found or opened | User notified; program is terminated |
| ValueError | Input file is empty | User notified; program is terminated |
| UnicodeDecodeError | Input file is not text | User notified; program is terminated |
| FileNotFoundError | Output file cannot be opened | User notified; program is terminated |
| IndexError | src> or dst> are not found in expected locations | User notified; RECV line ignored |
| ValueError | src or dst IP address is not valid | User notified; RECV line ignored |

#### IV - Logging

Exceptions are logged in the current directory as `d3js_error.log`.

#### V - Pre-planned Improvements
