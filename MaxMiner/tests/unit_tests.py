import unittest
import logging

import numpy

from MaxMiner.transactionalUtils import generate_transactional_encoder_from_collection
import MaxMiner

#Synthetic dataset was borrowed from the SPMF documentation for Charm-MFI, another maximal dataset miner
charm_mfi_spmf_in_data = [
    [1, 3, 4],
    [2, 3, 5],
    [1, 2, 3, 5],
    [2, 5],
    [1, 2, 3, 5],
] 

charm_mfi_spmf_out_data = [
    [1,2,3,5]
]

#Reversed engineered dataset from illustrations of the MAFIA algorithm from the original paper
# 8 rows 
mafia_paper_in_data = [
    [1,2,3,4], #Not included ~12%
    [1,2], #~36
    [1,2],
    [1,2],
    [2,3],
    [2,3],
    [2,3],
    [3,4],
    [3,4],
    [3,4],
]

mafia_paper_in_data_edge = [
    [1,2,3,4], #Not included ~12%
    [1,2], #~36
    [1,2],
    [1,2],
    [2,3],
    [2,3],
    [2,3],
    [3,4],
    [3,4],
    [3,4],
]

#Output of reverse engineered MAFIA data at 20% MinSp threshold
mafia_paper_out_data_mid_support = [
    [1,2],
    [2,3],
    [3,4]
]

#Alternate versions with 20% min threshold to test the HUMFI optimization 10%
mafia_paper_out_data_low_support = [
    [1,2,3,4]
]



class TestCalc(unittest.TestCase):
    def setUp(self):
        basic_format = "%(asctime)-15s %(message)s"
        logging.basicConfig(level=logging.DEBUG, format=basic_format)
    
    def test_encoder(self):
        transaction_encoder = generate_transactional_encoder_from_collection(mafia_paper_in_data)

        '''
        encoded_transactions, encoder_key = transaction_encoder.encode_horizontally_from_collection_frequent(mafia_paper_in_data, 0.2)
        maximal_itemsets = MaxMiner.MAFIA_on_encoded_collection(encoded_transactions, transaction_encoder, 0.2)
        logging.info("Maximal itemsets uncovered {}".format(maximal_itemsets))
        '''
        encoded_transactions, encoder_key = transaction_encoder.encode_horizontally_from_collection_frequent(mafia_paper_in_data, 0.05)
        maximal_itemsets = MaxMiner.MAFIA_on_encoded_collection(encoded_transactions, transaction_encoder, 0.05)
        logging.info("Maximal itemsets uncovered {}".format(maximal_itemsets))

