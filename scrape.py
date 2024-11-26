# project: MP3
# submitter: Max Mitchell
# partner: none
# hours: 12


## Import Statements ##
import os
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import requests
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
import time
## End Import Statements ##

class GraphSearcher:
    def __init__(self):
        self.visited = set()
        self.order = []

    def visit_and_get_children(self, node):
        """ Record the node value in self.order, and return its children
        param: node
        return: children of the given node
        """
        raise Exception("must be overridden in sub classes -- don't change me here!")


    def dfs_search(self, node):
        self.visited.clear()
        self.order.clear()
        self.dfs_visit(node)

    def dfs_visit(self, node):
        if node not in self.visited:
            self.visited.add(node)
            if '.txt' not in node:
                self.order.append(node)   # Record the visit
            children = self.visit_and_get_children(node)
            for child in children:
                self.dfs_visit(child)
            
                
    def bfs_search(self, start_node):
        self.visited.clear()
        self.order.clear()
        queue = [start_node]

        while queue:
            node = queue.pop(0)
            if node not in self.visited:
                self.visited.add(node)
                # For MatrixSearcher, append node directly. For FileSearcher, adjust based on your design.
                if '.txt' not in node:
                    self.order.append(node)   
                children = self.visit_and_get_children(node)
                for child in children:
                    if child not in self.visited:
                        queue.append(child)



class MatrixSearcher(GraphSearcher):
    def __init__(self, df):
        super().__init__()  # Initialize the base class
        self.df = df  # Adjacency matrix

    def visit_and_get_children(self, node):
        children = []
        # Iterate over the adjacency matrix row corresponding to `node`
        for child, has_edge in self.df.loc[node].items():
            if has_edge:  # If there's an edge from `node` to `child`
                children.append(child)
        # Note: No need to append to self.order here; it will be handled in the search methods
        return children


class FileSearcher(GraphSearcher):
    def __init__(self, directory="file_nodes"):
        super().__init__()
        self.directory = directory
        
    def visit_and_get_children(self, node):
        """Reads a node file, records its value in self.order, and returns a list of children."""
        node_path = os.path.join(self.directory, node)  # Construct full path to the file
        with open(node_path, 'r') as file:
            value = file.readline().strip()  # Read only the first line for the value
            children_line = file.readline().strip()  # Read the second line for children
            children = children_line.split(',') if children_line else []
        
        ##print(f"Visiting: {node}, Value: {value}, Children: {children}")
        self.order.append(value)  # Append the value from the file
    
        return children

        
    def concat_order(self):
        """Returns all the values concatenated together."""
        return ''.join(self.order)

    
class WebSearcher(GraphSearcher):
    def __init__(self, driver):
        super().__init__()
        self.driver = driver
        self.table_fragments = []

    def visit_and_get_children(self, node):
        self.driver.get(node)
        # Extract hyperlinks
        links = [element.get_attribute('href') for element in self.driver.find_elements(By.TAG_NAME, 'a') if element.get_attribute('href') is not None]
        
        # Extract table data
        try:
            # Read tables directly from the page source
            dfs = pd.read_html(self.driver.page_source)
            self.table_fragments.extend(dfs)  # Store table fragments for later use

        except ValueError:
            # No tables found
            pass
        # for df in self.table_fragments:
        #     print(df.head())  # Preview the first few rows of each table fragment
        #     print(df.columns)  # Print column names to identify any unexpected ones
        return links  # Return list of URLs

    def table(self):
        # Concatenate all table fragments into one DataFrame
        if self.table_fragments:
            # You might want to align the columns or filter out unnecessary ones before concatenating
            aligned_fragments = [df[['clue', 'latitude', 'longitude', 'description']] for df in self.table_fragments if 'clue' in df.columns]
            return pd.concat(aligned_fragments, ignore_index=True)
        else:
            return pd.DataFrame()

def reveal_secrets(driver, url, travellog):
    # Generate the password from the "clue" column
    password = travellog['clue'].astype(str).str.cat()

    # Navigate to the URL
    driver.get(url)

    # Wait for the clue input to be visible and then type the password
    wait = WebDriverWait(driver, 10)
    clue_input = wait.until(EC.visibility_of_element_located((By.ID, 'password-textbox')))
    clue_input.send_keys(password)


    # Click the "GO" button
    go_button = driver.find_element(By.ID, 'submit-button')
    go_button.click()
    time.sleep(5)

    # Wait for the "View Location" button to be clickable and then click it
    view_location_button = wait.until(EC.element_to_be_clickable((By.ID, 'view-location-button')))
    view_location_button.click()
    time.sleep(5)

    # Wait for the image to be visible
    image = wait.until(EC.visibility_of_element_located((By.ID, 'image')))
    image_url = image.get_attribute('src')

    # Download and save the image
    response = requests.get(image_url)
    print(response.content)
    with open('Current_Location.jpg', 'wb') as file:
        file.write(response.content)

    # Wait for the current location text to be present
    current_location = wait.until(EC.visibility_of_element_located((By.ID, 'location'))).text

    return current_location