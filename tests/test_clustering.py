import unittest
import numpy as np

from main import compute_centers

class TestClustering(unittest.TestCase):

    def test_compute_centers(self):
        '''Test the centers are correctly aggreagated based on
        labels using compute_centers.
        '''
        # Create a matrix with each list per line.
        data = np.vstack([[1,2], [4,5], [0,1]])
        labels1 = [0, 1, 0]
        centers1 = compute_centers(data, labels1)
        labels2 = [1, 0, 1]
        centers2 = compute_centers(data, labels2)

        # Convert data to float.
        data = data.astype(np.float)
        actual_centers1 = [ (data[0,:] + data[2,:]) / 2, data[1,:] ]
        for i, a in enumerate(actual_centers1):
            self.assertEqual(a.tolist(), centers1[i].tolist())

        actual_centers2 = [ data[1,:], (data[0,:] + data[2,:]) / 2 ]
        for i, a in enumerate(actual_centers2):
            self.assertEqual(a.tolist(), centers2[i].tolist())
