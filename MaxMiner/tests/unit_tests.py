import unittest
import logging

import numpy

from MaxMiner.transactionalUtils import generate_transactional_encoder_from_collection
import MaxMiner
from MaxMiner import rules

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

#Recreates the data and settings of the demo video at .5 minsup
charm_video_in_data = [
    [1, 2, 4, 5],
    [2, 3, 5],
    [1, 2, 4, 5],
    [1, 2, 3, 5],
    [1, 2, 3, 4, 5],
    [2, 3, 4]  
]

charm_video_out_data = [
    {1, 4, 5, 2},
    {1, 5, 2},
    {3, 5, 2},
    {3, 2},
    {4, 2},
    {5, 2},
]

#MinSup 50%
charm_paper_in_data = [
    ['A', 'C', 'T', 'W'],
    ['C', 'D', 'W'],
    ['A', 'C', 'T', 'W'],
    ['A', 'C', 'D', 'W'],
    ['A', 'C', 'D', 'T', 'W'],
    ['C', 'T', 'D'],

]

charm_paper_out_data = [
    {'C'},
    {'C', 'W'},
    {'C', 'D'},
    {'C', 'T'},
    {'A', 'C', 'W'},
    {'C', 'D', 'W'},
    {'A', 'C', 'T' ,'W'}
]


def setTester(algorithm_out_sets, expected_out_sets):
    '''
        Helper function for testing the entire output set of an IM algorithm
    '''
    
    valid_flag = True
    for expected_set in expected_out_sets:
        if expected_set not in algorithm_out_sets:
            valid_flag = False
    
    return valid_flag
    
    

class TestCalc(unittest.TestCase):
    def setUp(self):
        basic_format = "%(asctime)-15s %(message)s"
        logging.basicConfig(level=logging.INFO, format=basic_format)
    
    def test_encoder(self):
        transaction_encoder = generate_transactional_encoder_from_collection(mafia_paper_in_data)
        encoded_transactions, encoder_key = transaction_encoder.encode_horizontally_from_collection_frequent(mafia_paper_in_data, 0.05)


    '''
    def test_mafia(self):
        transaction_encoder = generate_transactional_encoder_from_collection(mafia_paper_in_data)

        encoded_transactions, encoder_key = transaction_encoder.encode_horizontally_from_collection_frequent(mafia_paper_in_data, 0.2)
        maximal_itemsets = MaxMiner.MAFIA_on_encoded_collection(encoded_transactions, transaction_encoder, 0.2)
        logging.info("Maximal itemsets uncovered {}".format(maximal_itemsets))

        encoded_transactions, encoder_key = transaction_encoder.encode_horizontally_from_collection_frequent(mafia_paper_in_data, 0.05)
        maximal_itemsets = MaxMiner.MAFIA_on_encoded_collection(encoded_transactions, transaction_encoder, 0.05)
        logging.info("Maximal itemsets uncovered {}".format(maximal_itemsets))
    
    '''
    def test_video_charm(self):
        transaction_encoder = generate_transactional_encoder_from_collection(charm_video_in_data)
        encoded_transactions, encoder_key = transaction_encoder.encode_horizontally_from_collection_frequent(charm_video_in_data, 0.5)
        
        num_transactions = encoded_transactions.shape[0]
        
        closed_itemsets = MaxMiner.CHARM_on_encoded_collection(encoded_transactions, transaction_encoder, 0.5)
        closed_itemsets_formatted = {}
        #self.assertTrue(setTester(closed_itemsets, charm_video_out_data))
        
        #output_rules = list(rules.generate_rules_apriori(closed_itemsets, 0.5, num_transactions))
        
        #print(output_rules)
        
    def test_paper_charm(self):
        transaction_encoder = generate_transactional_encoder_from_collection(charm_paper_in_data)
        encoded_transactions, encoder_key = transaction_encoder.encode_horizontally_from_collection_frequent(charm_paper_in_data, 0.5)
        closed_itemsets = MaxMiner.CHARM_on_encoded_collection(encoded_transactions, transaction_encoder, 0.5)
        
        #self.assertTrue(setTester(closed_itemsets, charm_paper_out_data))