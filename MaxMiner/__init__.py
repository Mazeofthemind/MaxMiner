import logging
import numpy as np
from numpy.core._multiarray_umath import bitwise_or
from _socket import close

def MAFIA_on_encoded_collection(encoded_transactions, transaction_encoder, min_support_ratio):
    '''
        Returns the Maximal Frequent Itemsets in a vertically encoded transaction database
        based on a provided minimum support ratio and the MAFIA algorithm.
        
        Requires a copy of the Transaction Encoder
        
        
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
                
                
                _MAFIA_recursive_candidate_assessor(candidate_set,
                    head_transactions, maximal_frequent_itemsets, frequent_item_sets, infrequent_item_sets, 
                    min_support_ratio, total_transaction_count)
    
    return maximal_frequent_itemsets

def _MAFIA_recursive_candidate_assessor(head_item_set: set, head_transactions, maximal_frequent_itemsets,
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
                    
                    _MAFIA_recursive_candidate_assessor(head_tail_items, head_tail_transactions, 
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

def CHARM_on_encoded_collection(encoded_transactions, transaction_encoder, min_support_ratio):
    '''
        CHARM performs two essential tasks finding frequent itemsets, and determining when an
        itemset is superceded by another itemset.
        
        The finished product when all frequent itemsets are generated and superceded is a list
        of closed itemsets.
    '''
    total_transaction_count = encoded_transactions.shape[0]

    decoder_map = transaction_encoder.value_decoder_mapping
    logging.debug(transaction_encoder.value_encoder_mapping)
    logging.debug(transaction_encoder.value_supports)
    
    closed_itemsets = []

        
    #Sorting the root items to be considered an order of ascending support as described in the paper
    sorted_root_candidates = sorted(transaction_encoder.value_supports.items(), key = 
                 lambda kv:(kv[1], kv[0]))
    sorted_root_candidate_items = list(map(lambda tuple: transaction_encoder.value_encoder_mapping[tuple[0]], sorted_root_candidates))
    
    logging.debug("Pre Encode {}, post encode {}".format(list(map(lambda item: item[0], sorted_root_candidates)), sorted_root_candidate_items))


    #Iterate through the root elements and compare them to all other root elements
    for root_item in sorted_root_candidate_items:
        
        #Create a holding variable to hold the superceded version of the root
        build_up_itemset = {root_item}
        
        for secondary_item in sorted_root_candidate_items:
            if secondary_item != root_item:
                
                #Isolate root and secondary item transactions 
                root_transactions = encoded_transactions[:,root_item]
                secondary_transactions = encoded_transactions[:,secondary_item]

                
                logging.debug("Checking subsumption for {} and {} (translated)".format(list(map(lambda x: decoder_map[x], build_up_itemset)), 
                    decoder_map[secondary_item]))

                #If the root item is subsumed by the secondary item, compound with root
                if _CHARM_subsumption_test(root_transactions, secondary_transactions):
                    previous_build_up_itemset = build_up_itemset.copy()
                    build_up_itemset.add(secondary_item)
                    logging.debug("{} is subsumed by {} making {} (translated)".format(list(map(lambda x: decoder_map[x], previous_build_up_itemset)), 
                                                                          decoder_map[secondary_item], 
                                                                          list(map(lambda x: decoder_map[x], build_up_itemset))))
                #Otherwise, treat the root and secondary as a potential new frequent itemset 
                else:
                    head_item_set = {root_item}
                    head_item_set.add(secondary_item)
                    
                    _CHARM_recursive_candidate_assessor(head_item_set, encoded_transactions, sorted_root_candidate_items, 
                        closed_itemsets, min_support_ratio, total_transaction_count)
        
        #Once we have iterated through all potentially superceding variables, add the compilation to closed itemsets
        closed_itemsets.append(build_up_itemset)

    #Debug for the finished itemset
    translated_closed_itemsets = []
    for closed_itemset in closed_itemsets:
        decoded_itemset = list(map(lambda item: decoder_map[item], closed_itemset))
        decoded_itemset_tuple = tuple(decoded_itemset)
        translated_closed_itemsets.append(decoded_itemset_tuple)
    logging.info("Discovered closed itemsets {}".format(translated_closed_itemsets))
    logging.info("Discovered closed itemsets {} deduped".format(set(translated_closed_itemsets)))
                

def _CHARM_subsumption_test(root_transactions, secondary_transactions):
    '''
        Function that returns whether the transactiosn representing the root items
        are subsumed by the transactions representing the secondary items
        
        Tidsets are a list of transaction ids where a specified itemset appeared,
        
        Subsumption is called for when the tidset of the root items is a subset of the
        secondary items tidset.
        
        a = {1,2,3}, b = {1,2,3,4} -> True
    '''
    #Test for subsumption by determining that the transactions in which the root item are present
    #are a subset of the items  
    
    
    combined_transaction_shape = root_transactions.shape
    
    new_shape = list(secondary_transactions.shape)
    new_shape.append(1)
    
    #For original round with two individual items
    if len(combined_transaction_shape) == 1:

        '''
        root_transactions = root_transactions.reshape(new_shape)
        secondary_transactions = secondary_transactions.reshape(new_shape)
        combined_transaction_shape = (combined_transaction_shape[0], 2)
        '''
    #For successive founds as root itemset grows
    else:
        #This turns it into a two stage process, turning the multiple columns into 1D
        root_transactions = np.bitwise_and.reduce(root_transactions, axis=1)
        combined_transaction_shape = (combined_transaction_shape[0], 2)
        
    transaction_or = bitwise_or(root_transactions, secondary_transactions)
    
    return np.array_equal(transaction_or, secondary_transactions)

    
def _CHARM_recursive_candidate_assessor(head_item_set: set, encoded_transactions, 
    sorted_root_candidate_items, closed_itemsets, min_support_ratio: float, total_transaction_count: int):
    '''
    
    '''
    
    logging.debug("Assessing potential frequent item set {}".format(head_item_set))
    head_item_list = list(head_item_set)
    #head_transactions = encoded_transactions[:,head_item_list]
    
    head_transactions = encoded_transactions[np.sum(encoded_transactions[:,head_item_list], axis=1) == len(head_item_list)]
    head_column_transactions = encoded_transactions[:,head_item_list]
    
    
    head_support = head_transactions.shape[0]
    logging.info("Head Item Set {} Support {}".format(head_item_set, head_support/total_transaction_count))
    
    #If Head Support is above the MinSupp ratio, continue to evaluate the node
    if head_support/total_transaction_count >= min_support_ratio:
        logging.debug("{} is frequent".format(head_item_set))
        
        potential_tails = np.bitwise_or.reduce(head_transactions, axis=0) 
        
        potential_tail_indices = []
        for index, column_digest_value in enumerate(potential_tails):
            if column_digest_value == 1:
                potential_tail_indices.append(index)
                
        #Provides a support ordered set of potential tail items filtered from the master list
        reduced_sorted_root_candidate_items = list(filter(lambda index: index in potential_tail_indices, sorted_root_candidate_items))
        
        build_up_itemset = head_item_set.copy()
        
        for tail_item in reduced_sorted_root_candidate_items:
            if tail_item not in head_item_set:
                tail_column_transactions = encoded_transactions[:,tail_item]
                if _CHARM_subsumption_test(head_column_transactions, tail_column_transactions):
                    previous_build_up_itemset = build_up_itemset.copy()
                    build_up_itemset.add(tail_item)
                    
                    logging.debug("{} is subsumed by {} making {}".format(previous_build_up_itemset, 
                                                                          tail_item, 
                                                                          build_up_itemset))
                #Otherwise test as another potential frequnet itemset
                else:
                    logging.debug("{} is not subsumed by {}".format(build_up_itemset, tail_item))
                    
                
                
        
        logging.debug("Inserting closed itemset {}".format(build_up_itemset))
        closed_itemsets.append(build_up_itemset)
        
    else:
        logging.debug("{} is infrequent".format(head_item_set))
        return
        
    

    
    