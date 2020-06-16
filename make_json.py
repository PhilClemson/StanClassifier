import numpy as np
import rpy2.robjects as robjects
import json
from datetime import date

stan_flags = ['data', 'parameters', 'model']

# Find first or last non-whitespace substring
#
# Inputs:
#       text_string - string containing substrings
#       reverse - boolean (True: select last "word", False: select first "word")
#
# Outputs:
#       return_string - selected substring
def remove_whitespace(text_string,reverse):
    len_string = len(text_string)
    if (len_string>1):
        if (reverse == False):
            # remove everything but the first "word"
            ind = 0
            while ind < len_string:
                if((text_string[ind] != ' ') and (text_string[ind] != '"')):
                    break
                else:
                    ind += 1
            start_ind = ind
            while ind < len_string:
                if((text_string[ind] == ' ') or (text_string[ind] == '"')):
                    break
                else:
                    ind += 1
        else:
            # remove everything but the last "word"
            ind = len_string-1
            while ind > 0:
                if((text_string[ind] != ' ') and (text_string[ind] != '"')):
                    break
                else:
                    ind -= 1
	    if (ind != len_string-1):
	        ind += 1
	    start_ind = ind
	    while start_ind > 0:
	        if((text_string[ind] == ' ') or (text_string[ind] == '"')):
	            break
	        else:
	            start_ind -= 1
	    start_ind += 1
        if(ind == start_ind):
            return_string = -1
        else:
            return_string = text_string[start_ind:ind]
    elif (text_string != ' ' and text_string != '"'):
        return_string = text_string
    else:
        return_string = -1
        
    return return_string

# Find first or last non-whitespace substring
#
# Inputs:
#       text_string - string containing substrings
#       reverse - boolean (True: select last "word", False: select first "word")
#
# Outputs:
#       return_string - selected substring
def find_name(text_string):
    return_string = ''
    ind = len(text_string)-1
    name_start = False
    size_term = False
    name_end = False
    while ind > 0:
	if (name_start == True):
	    if (text_string[ind] != ' '):
		return_string = text_string[ind] + return_string
		ind -= 1
	    else:
		name_end = True
	elif (size_term == True):
	    if (text_string[ind] == '['):
		return_string = ''
		size_term = False
		ind -= 1
	    else:
		ind -= 1
	elif (text_string[ind] == ']'):
	    size_term = True
	    ind -= 1
	elif (text_string[ind] != ';'):
	    if (text_string[ind] != ' '):
		name_start = True
	    else:
		ind -= 1
	else:
	    ind -= 1
	if (name_end == True):
	     break
    return_string = return_string
        
    return return_string

# Get the upper / lower bounds (if any) for a data variable / parameter defined in the stan file
#
# Inputs:
#       text_string - string containing the variable with possible bounds
#
# Outputs:
#       bounds - library containing up to 2 floats (bounds[0] = lower bound, bounds[1] = upper bound)
#                if no bounds are found then an empty library is returned
def get_bounds(text_string):
    bounds = {}
    if ('lower=' in text_string):
        low_ind1 = text_string.find('=') + 1
        if ('upper=' in text_string):
            low_ind2 = text_string.find(',')
            high_ind1 = text_string.rfind('=') + 1
            high_ind2 = text_string.find('>')
            high_text = remove_whitespace(text_string[high_ind1:high_ind2],False)
            if (is_number(high_text)):
                bounds[1] = float(high_text)
            else:
                Exception('Bounds provided do not have numeric values')
        else:
            low_ind2 = text_string.find('>')
        low_text = remove_whitespace(text_string[low_ind1:low_ind2],False)
        if (is_number(low_text)):
            bounds[0] = float(low_text)
        else:
            Exception('Bounds provided do not have numeric values')
    elif ('upper=' in text_string):
        high_ind1 = text_string.rfind('=') + 1
        high_ind2 = text_string.find('>')
        high_text = remove_whitespace(text_string[high_ind1:high_ind2],False)
        if (is_number(high_text)):
            bounds[1] = float(high_text)
        else:
            Exception('Bounds provided do not have numeric values')
    return bounds

# Parse line of text from stan file and store values corresponding to data / parameter variables
#
# Inputs:
#       text_line - string (line of stan file)
#
# Inputs / Outputs:
#       v_type - list of strings storing the variable types
#       v_size - list of strings / numbers storing the sizes of the variables
#       v_name - list of strings storing the names of the variables
#       v_bounds - list of libraries storing the bounds of the variables 
#       v_num - total number of variables found
def stan_read(text_line_raw,v_type,v_size,v_name,v_bounds,v_num):
    # first remove any comments
    ind = text_line_raw.find('//')
    if (ind == -1):
	ind = text_line_raw.find('\n')
	text_line = text_line_raw[:ind-1]
    else:
	text_line = text_line_raw[:ind-1]
    if ('int' in text_line):
        v_type.append('int')
        if ('[' in text_line):
            size_array = []
            if (text_line.count('[')>1):
                if (',' in text_line):
                    Exception('Int cannot have multiple dimensions')
                else:
                    size_array.append(text_line[text_line.find("[")+1:text_line.find(']')])
                ind = text_line.find(']')+1
                size_array.append(text_line[text_line[ind:].find("[")+ind+1:text_line[ind:].find(']')+ind])
            else:
                if (',' in text_line):
                    Exception('Int cannot have multiple dimensions')
                else:
                    size_array.append(text_line[text_line.find("[")+1:text_line.find(']')])
            v_size.append(size_array)
        else:
            v_size.append(1)
        v_name.append(find_name(text_line))
        bounds = get_bounds(text_line)
        v_bounds.append(bounds)
        v_num += 1
    elif ('real' in text_line):
        v_type.append('real')
        if ('[' in text_line):
            size_array = []
            if (text_line.count('[')>1):
                if (',' in text_line):
                    Exception('Real cannot have multiple dimensions')
                else:
                    size_array.append(text_line[text_line.find("[")+1:text_line.find(']')])
                ind = text_line.find(']')+1
                size_array.append(text_line[text_line[ind:].find("[")+ind+1:text_line[ind:].find(']')+ind])
            else:
                if (',' in text_line):
                    Exception('Real cannot have multiple dimensions')
                else:
                    size_array.append(text_line[text_line.find("[")+1:text_line.find(']')])
            v_size.append(size_array)
        else:
            v_size.append(1)
        v_name.append(find_name(text_line))
        bounds = get_bounds(text_line)
        v_bounds.append(bounds)
        v_num += 1
    elif ('vector' in text_line):
        v_type.append('vector')
        if ('[' in text_line):
            size_array = []
            if (text_line.count('[')>1):
                if (',' in text_line):
                    Exception('Vector cannot have multiple dimensions')
                else:
                    size_array.append(text_line[text_line.find("[")+1:text_line.find(']')])
                ind = text_line.find(']')+1
                size_array.append(text_line[text_line[ind:].find("[")+ind+1:text_line[ind:].find(']')+ind])
            else:
                if (',' in text_line):
                    Exception('Vector cannot have multiple dimensions')
                else:
                    size_array.append(text_line[text_line.find("[")+1:text_line.find(']')])
            v_size.append(size_array)
        else:
            raise Exception('Vector in stan file does not have a size')
        v_name.append(find_name(text_line))
        bounds = get_bounds(text_line)
        v_bounds.append(bounds)
        v_num += 1
    elif ('simplex' in text_line):
        v_type.append('simplex')
        if ('[' in text_line):
            size_array = []
            if (text_line.count('[')>1):
                if (',' in text_line):
                    Exception('Vector cannot have multiple dimensions')
                else:
                    size_array.append(text_line[text_line.find("[")+1:text_line.find(']')])
                ind = text_line.find(']')+1
                size_array.append(text_line[text_line[ind:].find("[")+ind+1:text_line[ind:].find(']')+ind])
            else:
                if (',' in text_line):
                    Exception('Vector cannot have multiple dimensions')
                else:
                    size_array.append(text_line[text_line.find("[")+1:text_line.find(']')])
            v_size.append(size_array)
        else:
            raise Exception('Vector in stan file does not have a size')
        v_name.append(find_name(text_line))
        bounds = get_bounds(text_line)
        v_bounds.append(bounds)
        v_num += 1
    elif ('ordered' in text_line):
        v_type.append('ordered')
        if ('[' in text_line):
            size_array = []
            if (text_line.count('[')>1):
                if (',' in text_line):
                    Exception('Vector cannot have multiple dimensions')
                else:
                    size_array.append(text_line[text_line.find("[")+1:text_line.find(']')])
                ind = text_line.find(']')+1
                size_array.append(text_line[text_line[ind:].find("[")+ind+1:text_line[ind:].find(']')+ind])
            else:
                if (',' in text_line):
                    Exception('Vector cannot have multiple dimensions')
                else:
                    size_array.append(text_line[text_line.find("[")+1:text_line.find(']')])
            v_size.append(size_array)
        else:
            raise Exception('Vector in stan file does not have a size')
        v_name.append(find_name(text_line))
        bounds = get_bounds(text_line)
        v_bounds.append(bounds)
        v_num += 1
    elif ('matrix' in text_line):
	v_type.append('matrix')
        if ('[' in text_line):
            size_array = []
            if (text_line.count('[')>1):
                if (',' in text_line):
                    size_array.append(text_line[text_line.find("[")+1:text_line.find(',')])
                    size_array.append(text_line[text_line.find(",")+1:text_line.find(']')])
                else:
                    # covariance matrix or similar
                    size_array.append(text_line[text_line.find("[")+1:text_line.find(']')])
                    size_array.append(text_line[text_line.find("[")+1:text_line.find(']')])
                ind = text_line.find(']')+1
                if (text_line[ind:].count('[')>1):
                    size_array.append(text_line[text_line[ind:].find("[")+ind+1:text_line[ind:].find(']')+ind])
                    ind = text_line[ind:].find(']')+1
                    size_array.append(text_line[text_line[ind:].find("[")+ind+1:text_line[ind:].find(']')+ind])
                else:
                    size_array.append(text_line[text_line[ind:].find("[")+ind+1:text_line[ind:].find(']')+ind])
            else:
                if (',' in text_line):
                    size_array.append(text_line[text_line.find("[")+1:text_line.find(',')])
                    size_array.append(text_line[text_line.find(",")+1:text_line.find(']')])
                else:
                    # covariance matrix or similar
                    size_array.append(text_line[text_line.find("[")+1:text_line.find(']')])
                    size_array.append(text_line[text_line.find("[")+1:text_line.find(']')])
            v_size.append(size_array)
        else:
            raise Exception('Matrix in stan file does not have a size')
        v_name.append(find_name(text_line))
        bounds = get_bounds(text_line)
        v_bounds.append(bounds)
        v_num += 1
    elif ('cholesky_factor' in text_line):
	v_type.append('cholesky_factor')
        if ('[' in text_line):
            size_array = []
            if (text_line.count('[')>1):
                if (',' in text_line):
                    Exception('Error in Cholesky factor syntax')
                else:
                    # covariance matrix or similar
                    size_array.append(text_line[text_line.find("[")+1:text_line.find(']')])
                    size_array.append(text_line[text_line.find("[")+1:text_line.find(']')])
                ind = text_line.find(']')+1
                if (text_line[ind:].count('[')>1):
                    size_array.append(text_line[text_line[ind:].find("[")+ind+1:text_line[ind:].find(']')+ind])
                    ind = text_line[ind:].find(']')+1
                    size_array.append(text_line[text_line[ind:].find("[")+ind+1:text_line[ind:].find(']')+ind])
                else:
                    size_array.append(text_line[text_line[ind:].find("[")+ind+1:text_line[ind:].find(']')+ind])
            else:
                if (',' in text_line):
                    Exception('Error in Cholesky factor syntax')
                else:
                    # covariance matrix or similar
                    size_array.append(text_line[text_line.find("[")+1:text_line.find(']')])
                    size_array.append(text_line[text_line.find("[")+1:text_line.find(']')])
            v_size.append(size_array)
        else:
            raise Exception('cholesky_factor in stan file does not have a size')
        v_name.append(find_name(text_line))
        bounds = get_bounds(text_line)
        v_bounds.append(bounds)
        v_num += 1
    return v_type,v_size,v_name,v_bounds,v_num

# Determines if string is a number
#
# Inputs:
#       n - string (potentially a number)
#
# Outputs:
#       boolean (True - string is a number, False - string is not a number)
def is_number(n):
    try:
        float(n)   # Type-casting the string to `float`.
                   # If string is not a valid `float`, 
                   # it'll raise `ValueError` exception
    except ValueError:
        return False
    return True

# Find a string in a string list without possibility of raising ValueError exception
#
# Inputs:
#       name - string to search for in the list
#       name_line - list of strings
#
# Outputs:
#       index - integer corresponding to the position of the string in the string in the list (returns -1 if not found)
def try_find(name,name_list):
    try:
        index = name_list.index(name)
    except ValueError:
        index = -1
    return index
    
# Gets the position and type of the first mathematical operator in a string
#
# Inputs:
#       string - string containing a mathematical expression
#
# Outputs:
#       return_ind - integer giving the position of next operator
#       return_operator - character of the next operator
def get_operator(string):
    # Get the next operator
    operator = ['/','*','+','-','(',')']
    return_ind = -1
    return_operator = -1
    for n in range(0,6):
        ind = string.find(operator[n])
        if (ind != -1):
            if (return_ind == -1):
                return_ind = ind
                return_operator = operator[n]
		k = ind + 1
		flag_end = False
		# check for operator-bracket combinations
		while (k < len(string)):
		    for m in range(0,6):
			if (string[k] == operator[m]):
			    return_operator += operator[m]
			    return_ind = k
			    flag_end = True
		    if (flag_end == True):
			break
		    elif (string[k] != ' '):
			break
		    else:
		        k += 1
            elif (ind < return_ind):
                return_ind = ind
                return_operator = operator[n]
		k = ind + 1
		flag_end = False
		# check for operator-bracket combinations
		while (k < len(string)):
		    for m in range(0,6):
			if (string[k] == operator[m]):
			    return_operator += operator[m]
			    return_ind = k
			    flag_end = True
		    if (flag_end == True):
			break
		    elif (string[k] != ' '):
			break
		    else:
		        k += 1
    return return_ind,return_operator

# Gets the size string of a parameter in a format which can be evaluated
#
# Inputs:
#       size_string - string containing a mathematical expression
#
# Outputs:
#       eval_string - size_string with any data names replaced with numbers
def get_eval_string(size_string,data_name,data_value):
    if (is_number(size_string) == True):
        eval_string = size_string
    else:
        eval_string = ' '
        next_ind = 0
        last_ind = 0
        while (last_ind < len(size_string)):
            [next_ind,operator] = get_operator(size_string[last_ind:])
            if (next_ind == -1):
                name = remove_whitespace(size_string[last_ind:],False)
		last_ind = len(size_string)
                if (is_number(name) == True):
                    eval_string += name
                else:
                    index = try_find(name,data_name)
                    if (index != -1):
                        eval_string += data_value[index]
                    else:
                        raise Exception('Unrecognised variable in parameter size definition')
            else:
                name = remove_whitespace(size_string[last_ind:last_ind+next_ind-len(operator)+1],False)
                index = try_find(name,data_name)
                if (is_number(name) == True):
                    eval_string += name + operator
                else:
                    index = try_find(name,data_name)
                    if (index != -1):
                        eval_string += data_value[index] + operator
                    else:
                        raise Exception('Unrecognised variable in parameter size definition')
                last_ind = last_ind + next_ind + 1
    return eval_string

# main function
def make_outfile(stan_file, data_file, author):

	print(stan_file)

	model_fname = stan_file[stan_file.rfind('/')+1:-5]
	data_fname = stan_file[data_file.rfind('/')+1:-5]

	f_stan = open(stan_file, 'r')
	stan_text = f_stan.readlines()

	# Parse stan file
	flag_data=False
	flag_parameters=False
	flag_model=False
	data_num=0
	param_num=0
	model_num=0
	param_type=[]
	data_type=[]
	param_name=[]
	data_name=[]
	param_size=[]
	data_size=[]
	param_bounds=[]
	data_bounds=[]
	v_mu=[]
	v_sigma=[]
	v_bounds=[]
	calc_order=[]
	for text_line in stan_text:
	    # highlight relevant sections
	    if ('data {' in text_line):
		if ('transformed' not in text_line):
			flag_data = True
	    elif ('parameters {' in text_line):
		if ('transformed' not in text_line):
		    flag_parameters = True
	    elif ('model {' in text_line):
		flag_model = True
	    # handle each section
	    elif (flag_data == True):
		if ('}' in text_line):
		    flag_data = False
		else:
		    [data_type,data_size,data_name,data_bounds,data_num]=stan_read(text_line,data_type,data_size,data_name,data_bounds,data_num)
	    elif (flag_parameters == True):
		if ('}' in text_line):
		    flag_parameters = False
		else:
		    [param_type,param_size,param_name,param_bounds,param_num]=stan_read(text_line,param_type,param_size,param_name,param_bounds,param_num)
		    
	f_stan.close()


	f_data = open(data_file, 'r')
	data_text = f_data.readlines()

	flag_array = False
	flag_start = False
	data_value = {}

	# Parse data file
	for text_line in data_text:
	    if ('<-' in text_line):
		if (flag_array == True):
		    flag_array = False
		    data_value[index] = np.array(robjects.reval(array_string))
		elif (flag_start == True):
		    Exception('Variable has unassigned value in data file')
		name_end = text_line.find('<')
		name = remove_whitespace(text_line[0:name_end],False)
		index = try_find(name,data_name)
		if (index != -1):
		    if (data_size[index] == 1):
			if ('c(' in text_line):
			    raise Exception('Specified data sizes do not match those in the data file')
			else:
			    value_start = text_line.rfind('-') + 1
			    value = remove_whitespace(text_line[value_start:],False)
			    if (is_number(value) == True):
				if (value[-1:] == '\n'):
				    data_value[index] = value[:-1]
				else:
				    data_value[index] = value
			    else:
				flag_start = True
		    else:
			if ('c(' in text_line):
			    flag_array = True
			    value_start = text_line.find('-') + 1
			    if (text_line[-2:] == '\n'):
				array_string = text_line[value_start:-3]
			    else:
				array_string = text_line[value_start:]
			else:
			    flag_start = True
	    elif (flag_array == True):
		if (text_line[-2:] == '\n'):
		    array_string += text_line[:-3]
		else:
		    array_string += text_line
	    elif (flag_start == True):
		if (data_size[index] == 1):
		    if ('c(' in text_line):
			raise Exception('Specified data sizes do not match those in the data file')
		    else:
			if (text_line[-1:] == '\n'):
			    value = remove_whitespace(text_line[:-1],False)
			else:
			    value = remove_whitespace(text_line,False)
			if (is_number(value) == True):
			    data_value[index] = value
			    flag_start = False
		else:
		    if ('c(' in text_line):
			flag_array = True
			#value_start = text_line.rfind('c')
			#array_string = text_line[value_start:]
			if (text_line[-2:] == '\n'):
			    array_string = text_line[:-3]
			else:
			    array_string = text_line
			flag_start = False

	if (flag_array == True):
		data_value[index] = np.array(robjects.reval(array_string))
		
	f_data.close()

	if len(data_value) != len(data_name):
	    raise Exception('Specified data sizes do not match those in the data file')

	eval_param_size=[]

	if (param_num>0):
	    for size_string in param_size:
		if (isinstance(size_string, int)):
		    eval_param_size.append(size_string)
		elif (isinstance(size_string, str)):
		    # not list, only one element to deal with
		    eval_param_size.append(eval(get_eval_string(size_string,data_name,data_value)))
		else:
		    eval_param_size.append(1)
		    for size_string_element in size_string:
			# evaluate elements and multiply together to get total size
			#print(get_eval_string(size_string_element,data_name,data_value))
			eval_param_size[-1] *= eval(get_eval_string(size_string_element,data_name,data_value))

	# get keywords from directory
	index = -1
	ind = 0
	keywords = []
	url = 'https://github.com/stan-dev/example-models'
	while ind < len(stan_file)-5:
	    if (stan_file[ind] == '/'):
		ind += 1
		index += 1
		if (ind < len(stan_file)-5):
		    keywords.append(stan_file[ind])
		    url += '/' + stan_file[ind]
		    ind += 1
		else:
		    url += '/'
		    break
	    elif (ind == 0):
		index += 1
		keywords.append(stan_file[ind])
		url += '/' + stan_file[ind]
		ind += 1
	    else:
		keywords[index] += stan_file[ind]
		url += stan_file[ind]
		ind += 1

	outf = open("{}.json".format(model_fname), "w")

	# write .json file
	outf.write('{\n')
	outf.write('  "name": "{}",\n'.format(model_fname))
	outf.write('  "keywords": {},\n'.format(json.dumps(keywords)))
	outf.write('  "urls": "{}",\n'.format(url))
	outf.write('  "model_name": "{}",\n'.format(model_fname))
	outf.write('  "data_name": "{}",\n'.format(data_fname))
	outf.write('  "reference_posterior_name": null,\n')
	outf.write('  "references": [],\n')
	outf.write('  "dimensions": {\n')
	if (len(param_name) > 1):
	    for n in range(0, len(param_name)-1):
		outf.write('    "{}": {},\n'.format(param_name[n],eval_param_size[n]))
	    outf.write('    "{}": {}\n'.format(param_name[-1],eval_param_size[-1]))
	else:
	    outf.write('    "{}": {}\n'.format(param_name[0],eval_param_size[0]))
	outf.write('  },\n')
	outf.write('  "added_date": "{}",\n'.format(date.today()))
	outf.write('  "added_by": "{}"\n'.format(author))
	outf.write('}')

