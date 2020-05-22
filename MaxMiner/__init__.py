import logging
import numpy as np

def MAFIA_on_encoded_collection(encoded_transactions, transaction_encoder, min_support_ratio):
    '''
        Accepts a Transaction Encoded ("vertical binary representation" according to the MAFIA
        paper) dataset, the encoder used to create it (which provides the original values for
        de-encoding) and the minimum support ratio
    '''
    #Generate intitial list of candidates from encoder keys
    #Note that these will already be filtered by min support during encoding phase
    root_candidates = transaction_encoder.value_encoder_mapping.values()

    total_transaction_count = encoded_transactions.shape[0]
    
    #Frequent itemsets that do not have any frequent supersets
    maximal_frequent_itemsets = set()
    
    #Evaluated itemsets which are found to be frequent or infrequent but not maximal
    frequent_item_sets = set()
    infrequent_item_sets = set()

    print(encoded_transactions)

    #Iterate through the first level candidates represented as column numbers
    for root_item in root_candidates:
        
        frequent_item_sets.add(root_item)
    
        #Filter transactions down to the rows pertinent to this root
        root_transactions = encoded_transactions[ encoded_transactions[:,root_item] == True]
        logging.info(root_transactions)
        
        #Identify tail items by bitwise_or columns and extracting those with positive values
        occupied_columns = np.bitwise_or.reduce(root_transactions, axis=0) 
        occupied_column_indices = []
        for index, column_digest_value in enumerate(occupied_columns):
            if column_digest_value == 1:
                occupied_column_indices.append(index)

        #Assess the "tail" (potential supersets) by sequentially choosing additional columns to evluate
        #and recursively following them
        for tail_item in occupied_column_indices:
            
            #Ensure that we do not assess the original candidate column
            if (tail_item != root_item):
                candidate_set = {root_item, tail_item}
                candidate_list = list(candidate_set)
                
                head_transactions = root_transactions[np.sum(root_transactions[:,candidate_list], axis=1) == len(candidate_set)]
                
                
                _recursive_candidate_assessor(candidate_set,
                    head_transactions, maximal_frequent_itemsets, frequent_item_sets, infrequent_item_sets, 
                    min_support_ratio, total_transaction_count)
    
    return maximal_frequent_itemsets

def _recursive_candidate_assessor(head_item_set: set, head_transactions, maximal_frequent_itemsets,
    frequent_item_sets, infrequent_item_sets, min_support_ratio: float, total_transaction_count: int):
    '''
        Recursive, depth-first search function that progressively assesses the tail of a root item through increasingly large supersets
        
        This assessor is designed to act on a base parent set (ex. {a, b}) and a a
    '''
    
    #Measure the support of the new head by measuring the support of the tail element within the transactions of the previous head
    
    
    head_support = head_transactions.shape[0]
    logging.info("Head Item Set {} Support {}".format(head_item_set, head_support/total_transaction_count))
    
    #If Head Support is above the MinSupp ratio, continue to evaluate the node
    if head_support/total_transaction_count > min_support_ratio:
        
        
        #Generate tail items from all occupied columns in the head's transactions
        occupied_columns = np.bitwise_or.reduce(head_transactions, axis=0) 
        tail_item_set = set()
        for index, column_digest in enumerate(occupied_columns):
            if column_digest == 1:
                tail_item_set.add(index)

        #Check to see if the head union tail is already present in the maximal frequent item list
        head_union_tail = tail_item_set.union(tail_item_set)
        if tuple(head_union_tail) in maximal_frequent_itemsets:
            logging.debug("HUTMFI Optimization Engaged")
            frequent_item_sets.add(tuple(head_item_set))
            return

        #If the head item set already contains its potential tail, it has no tail, and should be returned as a maximal set
        if len(head_item_set) == len(tail_item_set):
            logging.debug("No superset items found, {} is maximal".format(head_item_set))
            maximal_frequent_itemsets.add(tuple(head_item_set))
            return
        
        #Otherwise recursively evaluate the tail elements
        else:
            
            original_maximal_item_set_size = len(maximal_frequent_itemsets)
            
            for tail_item in tail_item_set:
                
                #Skip over items in the head item set
                maximal_itemsets = []
                if tail_item not in head_item_set:
                    
                    head_tail_items = head_item_set.copy()
                    head_tail_items.add(tail_item)
                    head_tail_items_list = list(head_tail_items)
                    
                    head_tail_transactions = head_transactions[np.sum(head_transactions[:,head_tail_items_list], axis=1) == len(head_tail_items_list)]
                    
                    _recursive_candidate_assessor(head_tail_items, head_tail_transactions, 
                        maximal_frequent_itemsets, frequent_item_sets, infrequent_item_sets, 
                        min_support_ratio, total_transaction_count)
                    
                    
            #After following all tail items, if we've found at least one maximal_itemset mark the current combination as depleted and return
            if len(maximal_frequent_itemsets) > original_maximal_item_set_size:
                logging.debug("Frequent/maximal tail items found")
                frequent_item_sets.add(tuple(head_item_set))
                return
            
            #Otherwise we assume that the tail elements were not frequent, and return the current head as a maximal itemset
            else:
                logging.debug("No frequent tail items found, {} is maximal".format(head_item_set))
                maximal_frequent_itemsets.add(tuple(head_item_set))
                return

    #If the Head is not above the MinSupp ratio the node should return itself as infrequent with no Maximal Itemsets
    else:
        logging.debug("Head items infrequent")
        infrequent_item_sets.add(tuple(head_item_set))
        return