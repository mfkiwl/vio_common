
#include "vio/TimeGrabber.h"
#include <sstream>
#include "vio/eigen_utils.h"
#include "vio/utils.h"

using namespace std;

namespace vio {

TimeGrabber::TimeGrabber()
    : last_line_index(-1), last_line_time(-1), isTimeFormatSet(false) {}
TimeGrabber::TimeGrabber(const string time_file_name) { init(time_file_name); }

TimeGrabber::~TimeGrabber() { time_stream.close(); }

bool TimeGrabber::isTimeAvailable() const { return time_stream.is_open(); }

bool TimeGrabber::init(const string time_file_name) {
  time_file = time_file_name;
  time_stream.open(time_file_name.c_str());
  last_line_index = -1;
  last_line_time = -1;
  isTimeFormatSet = false;
  if (!time_stream.is_open()) {
    std::cout << "Failed to open timestamp file:" << time_file_name << ".\n"
              << "This is OK if the time file is not provided intentionally."
              << std::endl;
    return false;
  } else {
    std::string tempStr;
    int headerLines = countHeaderLines(time_file_name);
    for (int jack = 0; jack < headerLines; ++jack)
      getline(time_stream, tempStr);
  }
  return true;
}

double TimeGrabber::readTimestamp(int line_number) {
  string tempStr;
  double precursor(-1);
  if (last_line_index > line_number) {
    cerr << "Reading previous timestamps is unsupported!" << endl;
    return -1;
  }
  if (last_line_index == line_number) return last_line_time;
  while (last_line_index < line_number) {
    if (!isTimeFormatSet) {
      time_stream >> precursor;
      isTimeInNanos = vio::isTimeInNanos(precursor);
      if (isTimeInNanos) {
        int64_t timeNanos = (int64_t)precursor;
        precursor = vio::nanoIntToSecDouble(timeNanos);
      }
      isTimeFormatSet = true;
    } else {
      if (isTimeInNanos) {
        int64_t timeNanos;
        time_stream >> timeNanos;
        precursor = vio::nanoIntToSecDouble(timeNanos);
      } else {
        time_stream >> precursor;
      }
    }

    if (time_stream.fail()) {
      break;
    }
    getline(time_stream, tempStr);  // remove the remaining part, this works
                                    // even when it is empty
    ++last_line_index;
  }
  if (last_line_index < line_number) {
    cerr << "Failed to find " << line_number << "th line in time file!" << endl;
    return -1;
  }
  last_line_time = precursor;
  return last_line_time;
}

// extract time from a text file
// for malaga dataset whose timestamps are in /*_IMAGE.txt file,
// every two lines are the left and right image names, typically with the same
// timestamp, e.g., img_CAMERA1_1261228749.918590_left.jpg
// img_CAMERA1_1261228749.918590_right.jpg
// img_CAMERA1_1261228749.968589_left.jpg
// img_CAMERA1_1261228749.968589_right.jpg
// Thus, frame number is 0 for the first two lines in the /*_IMAGE.txt file

// for indexed time file, each line is frame number, time in millisec

double TimeGrabber::extractTimestamp(int frame_number, bool isMalagaDataset) {
  string tempStr;
  double timestamp(-1);
  if (last_line_index > frame_number) {
    cerr << "Read previous timestamps is unsupported!" << endl;
    return -1;
  }
  if (last_line_index == frame_number) {
    return last_line_time;
  }
  while (last_line_index < frame_number) {
    getline(time_stream, tempStr);
    if (time_stream.fail()) break;
    if (isMalagaDataset) {
      last_left_image_name = tempStr;
      getline(time_stream, tempStr);  // read in the right image name
      timestamp = -1;
      timestamp = atof(tempStr.substr(12, 17).c_str());
    } else {  // frame index and timestamp in millisec
      std::istringstream iss(tempStr);
      int frameIndex(-1);
      timestamp = -1;
      iss >> frameIndex >> timestamp;
      timestamp *= 0.001;
    }
    ++last_line_index;
  }
  if (last_line_index < frame_number) {
    cerr << "Failed to find " << frame_number << "th line in time file!"
         << endl;
    return -1;
  }
  last_line_time = timestamp;
  return last_line_time;
}

}  // namespace vio
