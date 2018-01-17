
import numpy as np
import numpy.ma as ma

def _index_of_point(x, y, X, Y):
    if not ((x[0] <= X <= x[-1]) and (y[0] <= Y <= y[-1])):
        raise ValueError('Point ({0}, {1}) not contained in the gridded data'
                         .format(X, Y))

    i = int((Y - y[0]) / (y[1] - y[0]))
    j = int((X - x[0]) / (x[1] - x[0]))

    return min(i, len(y) - 2), min(j, len(x) - 2)


def _is_missing(q, i, j):
    return any([q[k, l] is ma.masked for k in (i, i+1) for l in (j, j+1)])


def _bilinear_interp(q, X, Y):
    x, y = q.x, q.y
    i, j = _index_of_point(x, y, X, Y)
    if _is_missing(q.data, i, j):
        raise ValueError('Not enough data to interpolate value at ({0}, {1})'
                         .format(X, Y))

    ax, ay = (X - x[j])/(x[1] - x[0]), (Y - y[i])/(y[1] - y[0])
    dq_dx = q[i, j+1] - q[i, j]
    dq_dy = q[i+1, j] - q[i, j]
    d2q_dx_dy = q[i, j] + q[i+1, j+1] - q[i+1, j] - q[i, j+1]

    return q[i, j] + ax*dq_dx + ay*dq_dy + ax*ay*d2q_dx_dy


class GridData(object):
    """Class for data sets defined on a regular spatial grid
    """

    def __init__(self, x, y, data, *, mask=None, missing_data_value=None):
        """Create a new gridded data set

        There are several ways to specify the missing data mask:
        * pass in a numpy masked array for the `data` argument
        * pass in the array `mask` of boolean values to indicate where data
          is missing
        * pass in a specific value `missing_data_value` indicating that any
          entry in `data` with this exact value is actually a missing data
          point

        Parameters
        ----------
        x, y : np.ndarray
            coordinates of the grid points
        data : np.ndarray or ma.MaskedArray
            values of the gridded data set
        mask : ndarray of bool, optional
            array describing missing data values; `True` indicates missing
        missing_data_value : float, optional
            value in `data` to indicate missing data
        """
        ny, nx = data.shape
        if (len(x) != nx) or (len(y) != ny):
            raise ValueError('Incompatible input array sizes')

        self.x = x
        self.y = y

        if isinstance(data, ma.MaskedArray):
            self.data = data
        elif missing_data_value is not None:
            self.data = ma.masked_equal(data, missing_data_value)
        elif mask is not None:
            self.data = ma.MaskedArray(data=data, mask=mask)
        else:
            raise ValueError()

    def __getitem__(self, indices):
        """Retrieve a given entry from the raw data
        """
        i, j = indices
        return self.data[i, j]

    def is_masked(self, x):
        """Returns `True` if the data cannot be interpolated to a point
        """
        i, j = _index_of_point(self.x, self.y, x[0], x[1])
        return _is_missing(self.data, i, j)

    def subset(self, xmin, ymin, xmax, ymax):
        """Return a sub-sample of a gridded dataset for the region between
        two points
        """
        Xmin, Ymin = max(xmin, self.x[0]), max(ymin, self.y[0])
        Xmax, Ymax = min(xmax, self.x[-1]), min(ymax, self.y[-1])

        imin, jmin = _index_of_point(self.x, self.y, Xmin, Ymin)
        imax, jmax = _index_of_point(self.x, self.y, Xmax, Ymax)

        x = self.x[jmin:jmax + 2]
        y = self.y[imin:imax + 2]
        data = self.data[imin:imax + 2, jmin:jmax + 2]
        return GridData(x, y, data)

    def __call__(self, x):
        """Evaluate the gridded data set at a given point
        """
        return _bilinear_interp(self, x[0], x[1])
