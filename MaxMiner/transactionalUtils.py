from typing import Iterable, Set, List, Dict, ClassVar, Tuple
import numpy as np
import logging

class TransactionalEncoder:
	'''
		Takes a dictionary of unique values and their supports, along with the total number of 
		transaction sets (rows). 
		
		This allows the encoder to both encode the data and filter values not relevant 
		to the calculation at hand based on their known support
	'''
	value_encoder_mapping:ClassVar[Dict[str, int]]
	value_supports:Dict[str, int]
	number_of_transactions:ClassVar[int]
	
	def __init__(self, unique_value_supports:Dict[str, int], number_of_transactions:int):
		'''
		
		'''
		
		self.value_supports = unique_value_supports
		
		self.value_encoder_mapping = {}
		for count, value in enumerate(unique_value_supports):
			self.value_encoder_mapping[value] = count
		
		self.number_of_transactions = number_of_transactions
	
	def encode_horizontally_from_csv (self, file_path:str):
		'''
			Load transaction data from a csv into a horizontally encoded binary numpy array for
			use with Apriori
		'''

		with open(file_path, 'r') as input_file:
			return self._base_hoz_encoder(input_file, True)
	
	def encode_horizontally_from_collection_frequent(self, iterable_object:Iterable, min_support_ratio_threshhold:float=0):
	#-> Tuple[np.ndarray, dict[str, int]]:
		'''
			Transaction data encoder for the Apriori-Frequent algorithm 

			Accepts an Iterable Python collection (presumably List of Lists) and converts it into a 
			Transaction Encoded 2D Numpy Array to be run through a CPU/GPU accelerated ARM algorithm
		
			Accepts a minimum support ratio threshold and uses it to pre-generate item supports and filter the
			transactions
		'''
		horizontally_encoded_array, valid_output_items, valid_combination_items = self._base_hoz_encoder(iterable_object, 
			False, 0, min_support_ratio_threshhold)
		return (horizontally_encoded_array, valid_output_items)
	
	def encode_horizontally_from_collection_inverse(self, iterable_object:Iterable, max_support_ratio_threshhold:float=0):
		'''
			Transaction data encoder for the Apriori-Inverse algorithm 
		
			Accepts a maximum support ratio threshold and uses it to pre-generate item supports and filter the
			transactions
		'''
		#Remove the valid_combination_items which is unused for Apriori Inverse
		horizontally_encoded_array, valid_output_items, valid_combination_items = self._base_hoz_encoder(iterable_object, 
			False, max_support_ratio_threshhold, 0)
		return (horizontally_encoded_array, valid_output_items) 
		
	def encode_horizontally_from_collection_rare(self, iterable_object:Iterable, max_support_ratio_threshhold:float=0, 
		min_support_ratio_threshold:float=0):
		'''
			Transaction data encoder for the Apriori-Rare algorithm 
			
			It's distinctive feature is accepting both a minimum and maximum support ratio threshold and producing
			both an output and combination  
			
			 which can also generate the support of individual items and filter based on that support. As such
		'''
		return self._base_hoz_encoder(iterable_object, False, max_support_ratio_threshhold, min_support_ratio_threshold)
	
	def _base_hoz_encoder(self, iterable_object:Iterable, csv_flag:bool, max_support_ratio_threshhold:float=0, min_support_ratio_threshhold:float=0):
	#-> Tuple[np.ndarray, dict[str, int]]:
				
		#These are two sets of single items and supports calculated by the encoder to
		#Use as the first set of output for the analytic
		#Combined by later stages of the algorithm
		#For Apriori Frequent and Inverse, these sets are identical, for Rare they are not
		valid_output_items = {}
		valid_combination_items = {}
		
		#If both thresholds are provided, assume we are preparing for Apriori rare and generate both the initial outputs and component items
		if max_support_ratio_threshhold > 0 or min_support_ratio_threshhold > 0:
			for value in self.value_supports:
				support = self.value_supports[value]
				support_ratio = support/self.number_of_transactions			
				
				logging.debug("{} {}".format(value, support_ratio))
				
				#Apriori Rare
				if max_support_ratio_threshhold > 0 and min_support_ratio_threshhold > 0:
					
					# If item is below the maximum support add to the output set but remove from the encoder
					if support_ratio < max_support_ratio_threshhold:
						valid_output_items[value] = support
						self.value_encoder_mapping.pop(value)
					# If item is above the min support, add to the combination set and keep in the encoder
					if support_ratio >= min_support_ratio_threshhold:
						valid_combination_items[value] = support
						
				#Apriori Inverse
				elif max_support_ratio_threshhold > 0:
					if support_ratio <= max_support_ratio_threshhold:
						valid_combination_items[value] = support
						valid_output_items[value] = support
					else:
						self.value_encoder_mapping.pop(value)
				
				
				#Apriori Frequent
				elif min_support_ratio_threshhold > 0:
					if support_ratio >= min_support_ratio_threshhold:
						valid_combination_items[value] = support
						valid_output_items[value] = support
					else:
						self.value_encoder_mapping.pop(value)
						
		logging.debug("Reduced items of interest from {} to {}".format(len(self.value_supports), len(self.value_encoder_mapping)))
		
		#Renumber lookup index to compensate for removed entries
		for index, key in enumerate(self.value_encoder_mapping.keys()):
			self.value_encoder_mapping[key] = index
		
		number_of_cols = len(self.value_encoder_mapping)
			
		horizontally_encoded_array = np.zeros((self.number_of_transactions, number_of_cols), dtype=bool)
		
		for col_index, row in enumerate(iterable_object):
			#Process CSV data
			if csv_flag == True:
				for value in row.split(','):
					value = value.strip()

					#If value is in encoder mapping, add to encoded data, otherwise discard
					if value in self.value_encoder_mapping:
						row_index = self.value_encoder_mapping[value]
						horizontally_encoded_array[col_index][row_index] = True
				
			#Process Python collections
			elif csv_flag == False:
				for value in row:

					#If value is in encoder mapping, add to encoded data, otherwise discard
					if value in self.value_encoder_mapping:
						row_index = self.value_encoder_mapping[value]
						horizontally_encoded_array[col_index][row_index] = True

		return (horizontally_encoded_array, valid_output_items, valid_combination_items)
	
	def encode_vertically_from_csv(self, file_path:str):
		'''
			Load transaction data from a csv into a vertically encoded binary numpy array for
			use with Apriori
		
		'''
		with open(file_path, 'r') as input_file:
			return self._base_vert_encoder(input_file, True)
					
	def encode_vertically_from_collection(self, iterable_object:Iterable):
		'''
			Load transaction data from a csv into a vertically encoded binary numpy array for
			use with Apriori
		
		'''
		return self._base_vert_encoder(iterable_object, False)
	
	def _base_vert_encoder(self, iterable_object:Iterable, csv_flag:bool) -> np.array:
		number_of_rows = len(self.value_encoder_mapping)
		vertically_encoded_array = np.zeros((number_of_rows, self.number_of_transactions), dtype=bool)
		
		for col_index, row in enumerate(iterable_object):
			if csv_flag == True:
				for value in row.split(','):
					value = value.strip()
					row_index = self.value_encoder_mapping[value]
					vertically_encoded_array[row_index][col_index] = True					
			elif csv_flag == False:
				for value in row:
					row_index = self.value_encoder_mapping[value]
					vertically_encoded_array[row_index][col_index] = True
		
		return vertically_encoded_array
def generate_transactional_encoder_from_csv(file_path:str):
	'''
		Generates a Transactional Encoder from a file containing Transaction data
		
		Expected format is newline rows containing non-fixed length, comma separated lists of categorical values,
		which are assumed to be strings
		
		##
		a,b,c
		a,c
		a,d
		##
	'''
	
	unique_values = set()
	number_of_transactions = 0
	with open(file_path, 'r') as input_file:
		for line in input_file:
			for item in line.split(','):
				item = item.strip()
				unique_values.add(item)
			number_of_transactions += 1
		
	print("{} num transactions".format(number_of_transactions))
	return TransactionalEncoder(unique_values, number_of_transactions)

def generate_transactional_encoder_from_collection(iterable_object:Iterable):
	'''
		Generates a Transactional Encoder from Python Collection of Transaction Data
		
		Expected input format is a Python List-of-Lists containing an arbitrary number of Python
		primitive (String, Float, Int) values.
		
		Generating the encoder includes three basic tasks: 
		
		-Identifying all unique items in the transaction set
		-Counting the total number of transactions
		-Combining these to determine which unique items have the required support and should be included 
		
		##
		[
		['a','b','c'],
		['a','c'],
		['a','d']
		]
		##
	'''
	unique_value_supports = {}
	number_of_transactions = 0
	for row in iterable_object:
		for value in row:
			if value not in unique_value_supports:
				unique_value_supports[value] = 0
			unique_value_supports[value] += 1
		number_of_transactions += 1
		
	return TransactionalEncoder(unique_value_supports, number_of_transactions)