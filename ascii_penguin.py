"""
ASCII Penguin Module
Provides ASCII art penguin for the Medical Inventory System.
"""

def get_penguin():
    """
    Returns an ASCII art penguin as a string.
    
    Returns:
        str: ASCII art representation of a penguin
    """
    penguin = r"""
       _~_
      (o o)
     /  V  \
    /|  |  |\
   ( |  |  | )
      ^^ ^^
    """
    return penguin

def display_penguin():
    """
    Prints the ASCII penguin to the console.
    """
    print(get_penguin())

if __name__ == "__main__":
    # When run directly, display the penguin
    display_penguin()
