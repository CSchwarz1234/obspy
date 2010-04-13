import os
import numpy as np
from obspy.core import UTCDateTime
from numpy.ma import is_masked
import pickle
from copy import deepcopy

class WaveformHandler(object):
    """
    Class that handles the caching or retrieving of the data for all waveforms.
    """
    def __init__(self, env, *args, **kwargs):
        self.env = env
        # Empty dict to handle the waveforms.
        self.waveforms = {}

    def getItem(self, network, station, location, channel):
        """
        Will check whether the requested waveform is already available in the cache
        directory and otherwise fetch it from a SeisHub Server. It will always
        return one stream object for one channel with the as many items as
        self.env.details.
        
        The cache directory has the following structure:

        cache
        L-- network
            L-- station
                L-- channel[location]--starttime_timestamp--endtime_timestamp.cache
        """
        network = str(network)
        station = str(station)
        location = str(location)
        channel = str(channel)
        id = '%s.%s.%s.%s' % (network, station, location, channel)
        if id in self.waveforms:
            stream = self.waveforms[id]['org_stream']
        # Otherwise get the waveform.
        stream = self.getWaveform(network, station, location, channel, id)
        self.waveforms[id] = {}
        self.waveforms[id]['org_stream'] = stream
        if not stream:
            self.waveforms[id]['empty'] = True
            return self.waveforms[id]
        self.waveforms[id]['empty'] = False
        # Process the stream_object.
        self.waveforms[id]['minmax_stream'] =\
                self.processStream(self.waveforms[id]['org_stream'])
        return self.waveforms[id]

    def processStream(self, stream):
        """
        Returns a min_max_list.
        """
        pixel = self.env.detail
        stream = deepcopy(stream)
        # Trim to times.
        stream.trim(self.env.starttime, self.env.endtime, pad = True)
        length = len(stream[0].data)
        # For debugging purposes. This should never happen!
        if len(stream) != 1:
            print stream
            raise
        # Reshape and calculate point to point differences.
        per_pixel = int(length//pixel)
        data = stream[0].data
        ptp = data[:pixel * per_pixel].reshape(pixel, per_pixel).ptp(axis=1)
        # Last pixel.
        last_pixel = data[pixel * per_pixel:]
        if len(last_pixel):
            last_pixel = last_pixel.ptp()
            if ptp[-1] < last_pixel:
                ptp[-1] = last_pixel
        ptp = ptp.astype('float32')
        # Create a logarithmic axis.
        if self.env.log_scale:
            ptp += 1
            ptp = np.log(self.ptp)/np.log(self.env.log_scale)
        # Make it go from 0 to 100.
        ptp *= 100.0/ptp.max()
        # Set masked arrays to zero.
        if is_masked(ptp):
            ptp.fill_value = 0.0
            ptp = ptp.filled()
        # Assure that very small values are also visible. Only true gaps are 0
        # and will stay 0.
        ptp[(ptp > 0) & (ptp < 0.5)] = 0.5
        stream[0].data = ptp
        return stream

    def getWaveform(self, network, station, location, channel, id):
        """
        Gets the waveform. Loads it from the cache or requests it from SeisHub.
        """
        # Go through directory structure and create all necessary
        # folders if necessary.
        network_path = os.path.join(self.env.cache_dir, network)
        if not os.path.exists(network_path):
            os.mkdir(network_path)
        station_path = os.path.join(network_path, station)
        if not os.path.exists(station_path):
            os.mkdir(station_path)
        files = os.listdir(station_path)
        # Remove all unwanted files.
        files = [file for file in files if file[-7:] == '--cache' and
                 file.split('--')[0] == '%s[%s]' % (channel, location)]
        # If no file exists get it from SeisHub. It will also get cached for
        # future access.
        if len(files) == 0:
            if self.env.debug:
                print ' * No cached file found for %s.%s.%s.%s' \
                    % (network, station, location, channel)
            stream = self.getPreview(network, station, location, channel,
                                      station_path)
            return stream
        else:
            # Otherwise figure out if the requested time span is already cached.
            times = [(float(file.split('--')[1]), float(file.split('--')[2]),
                      os.path.join(station_path, file)) for file in files]
            starttime = self.env.starttime.timestamp
            endtime = self.env.endtime.timestamp
            # Times should be sorted anyway so explicit sorting is not necessary.
            # Additionally by design there should be no overlaps.
            missing_time_frames = []
            times = [time for time in times if time[0] <= endtime and time[1] >=
                     starttime]
            if starttime < times[0][0]:
                missing_time_frames.append((starttime, times[0][0] +
                                            self.env.buffer))
            for _i in xrange(len(times) - 1):
                missing_time_frames.append((times[_i][1] - self.env.buffer,
                                times[_i + 1][0] + self.env.buffer))
            if endtime > times[-1][1]:
                missing_time_frames.append((times[-1][1] - self.env.buffer,
                                            endtime))
            # Load all cached files.
            stream = self.loadFiles(times)
            # Get the gaps.
            if missing_time_frames:
                if self.env.debug:
                    print ' * Only partially cached file found for %s.%s.%s.%s.' \
                          % (network, station, location, channel) +\
                          ' Requesting the rest from SeisHub...'
                stream += self.loadGaps(missing_time_frames, network, station,
                                        location, channel)
                if not stream:
                    msg = 'No data available for %s.%s.%s.%s for the selected timeframes'\
                        % (network, station, location, channel)
                    self.win.status_bar.setError(msg)
                    return
            else:
                if self.env.debug:
                    print ' * Cached file found for %s.%s.%s.%s' \
                        % (network, station, location, channel)
            # Merge everything and pickle once again.
            stream.merge(method = 1, interpolation_samples = -1)
            # Pickle the stream object for future reference. Do not pickle it if it
            # is smaller than 200 samples. Just not worth the hassle.
            if stream[0].stats.npts > 200:
                # Delete all the old files.
                for _, _, file in times:
                    os.remove(file)
                filename = os.path.join(station_path, '%s[%s]--%s--%s--cache' % \
                            (channel, location, str(stream[0].stats.starttime.timestamp),
                             str(stream[0].stats.endtime.timestamp)))
                file = open(filename, 'wb')
                pickle.dump(stream, file, 2)
                file.close()
            return stream

    def loadGaps(self, frames, network, station, location, channel):
        """
        Returns a stream object that will contain all time spans from the
        provided list.
        """
        streams = []
        for frame in frames:
            temp = self.env.seishub.getPreview(network, station, location,
                        channel, UTCDateTime(frame[0]), UTCDateTime(frame[1]))
            # Convert to float32
            if len(temp):
                temp[0].data = np.require(temp[0].data, 'float32')
                streams.append(temp)
        if len(streams):
            stream = streams[0]
            if len(streams) > 1:
                for _i in streams[1:]:
                    stream += _i
        else:
            stream = Stream()
        return stream

    def loadFiles(self, times):
        """
        Loads all necessary cached files.
        """
        streams = []
        for _t in times:
            file = open(_t[2], 'rb')
            streams.append(pickle.load(file))
            file.close()
        stream = streams[0]
        if len(streams) > 1:
            for _i in streams[1:]:
                stream += _i
        return stream

    def getPreview(self, network, station, location, channel, station_path,
                starttime = None, endtime = None):
        """
        Actually get the file.
        """
        stream = self.env.seishub.getPreview(network, station, location,
                 channel, starttime, endtime)
        if not len(stream):
            return None
        # It will always return exactly one Trace. Make sure the data is in
        # float32.
        stream[0].data = np.require(stream[0].data, 'float32')
        # Pickle the stream object for future reference. Do not pickle it if it
        # is smaller than 200 samples. Just not worth the hassle.
        if stream[0].stats.npts > 200:
            filename = os.path.join(station_path, '%s[%s]--%s--%s--cache' % \
                        (channel, location, str(stream[0].stats.starttime.timestamp),
                         str(stream[0].stats.endtime.timestamp)))
            file = open(filename, 'wb')
            pickle.dump(stream, file, 2)
            file.close()
        return stream