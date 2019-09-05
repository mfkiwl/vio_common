#!/usr/bin/env python
import argparse
import sys

import utility_functions

def parseArgs():
    # setup the argument list
    parser = argparse.ArgumentParser(
        description='Convert a pose file to standard format.')
    # case 1 arguments used by the kalibr to create a rosbag from a folder
    parser.add_argument('--infile',
                        help='A file containing rows of states, each state including '
                             'time, position and quaternion.\n'
                             'Time may be in secs or nanosecs, may at index 1 or 2.'
                             ' Quaternion may be xyzw or wxyz.\n'
                             'Positions always precede quaternions.')
    parser.add_argument('--in_quat_order',
                        default="xyzw", help="e.g., 'xyzw' or 'wxyz' (default: %(default)s)")
    parser.add_argument('--in_time_unit',
                        default=None,
                        help="e.g., 'ns', 'us', 'ms', 's'. If not provided, it will be determined"
                             " from the input data as either 's' or 'ns'. (default: %(default)s)")

    parser.add_argument('--outfile',
                        default="infile.out", help='ROS bag file (default: %(default)s)')

    parser.add_argument('--output_format',
                        default="TUM_RGBD",
                        help='Only KALIBR or TUM_RGBD are supported at the moment.\n'
                             'KALIBR: [t[nanos], x[m], y[m], z[m], q_x, q_y, q_z, q_w]\n'
                             'TUM_RGBD: [t[s] x[m] y[m] z[m] q_x q_y q_z q_w]\n'
                             '(default: %(default)s)')
    parser.add_argument('--output_delimiter',
                        default=',',
                        help="e.g., ',' or ' ' (default: %(default)s)")

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)
    parsed = parser.parse_args()
    return parsed

def convert_pose_format(infile, outfile, in_time_unit=None, in_quat_order="xyzw",
                        output_format="KALIBR", output_delimiter=","):
    # check infile line format
    with open(infile, "rb") as stream:
        lines = []
        max_lines = 2
        read_next = True
        line = None
        while read_next:
            line = stream.readline()
            read_next = utility_functions.is_header_line(line)
            if not read_next and len(lines) < max_lines:
                lines.append(line)
                read_next = True

        in_delimiter = utility_functions.decide_delimiter(lines[-1])
        time_index, time_unit, r_index = \
            utility_functions.decide_time_index_and_unit(lines, in_delimiter)

        if in_time_unit is not None:
            time_unit = in_time_unit
        print("The determined time index {} time unit {} and position index {}".format(
            time_index, time_unit, r_index))
    q_index = r_index + 3

    # load infile and write outfile
    with open(outfile, "w") as ostream:
        with open(infile, "rb") as istream:
            for line in istream:
                if utility_functions.is_header_line(line):
                    continue
                rags = line.split(in_delimiter)
                rags = [rag.strip() for rag in rags]
                secs, nanos = utility_functions.parse_time(rags[time_index])

                if output_format == "KALIBR":
                    if secs > 0:
                        ostream.write("{}{:09d}".format(secs, nanos))
                    else: # secs == 0
                        ostream.write("{}".format(nanos))
                elif output_format == "TUM_RGBD":
                    if secs > 0:
                        ostream.write("{}.{:09d}".format(secs, nanos))
                    else: # secs == 0
                        ostream.write("{}".format(float(nanos) / utility_functions.SECOND_TO_NANOS))
                else:
                    raise ValueError("Unsupported output format {}!".format(output_format))

                for j in range(3):
                    ostream.write("{}{}".format(output_delimiter, rags[r_index + j]))
                quat = utility_functions.normalize_quat_str(rags[q_index:q_index+4])
                if in_quat_order == "xyzw":
                    for j in range(4):
                        ostream.write("{}{}".format(output_delimiter, quat[j]))
                    ostream.write("\n")
                elif in_quat_order == "wxyz":
                    for j in range(3):
                        ostream.write("{}{}".format(output_delimiter, quat[j + 1]))
                    ostream.write("{}{}\n".format(output_delimiter, quat[0]))
                else:
                    raise ValueError("Unsupported input quaternion order {}!".format(in_quat_order))

def main():
    parsed = parseArgs()
    convert_pose_format(parsed.infile, parsed.outfile, parsed.in_time_unit, parsed.in_quat_order,
                        parsed.output_format, parsed.output_delimiter)


if __name__ == "__main__":
    main()
