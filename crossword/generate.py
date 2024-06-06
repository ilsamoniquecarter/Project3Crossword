import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for variable in self.domains:
        # Get the length of the word for the variable
        word_length = len(variable)
        
        # Remove values from the domain that are not consistent with the word length
        self.domains[variable] = {value for value in self.domains[variable] if len(value) == word_length}

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        revised = False
    # Get the overlap between variables x and y
    overlap = self.crossword.overlaps[x, y]
    if overlap is not None:
        x_index, y_index = overlap
        # Iterate over each value in the domain of x
        for x_value in list(self.domains[x]):
            # Check if there is any possible value in the domain of y that does not conflict with x_value
            if not any(x_value[x_index] == y_value[y_index] for y_value in self.domains[y]):
                # Remove x_value from the domain of x if there is no corresponding value in the domain of y
                self.domains[x].remove(x_value)
                revised = True
    return revised

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        # Initialize the queue of arcs
    queue = arcs if arcs is not None else [(x, y) for x in self.crossword.variables for y in self.crossword.neighbors(x)]
    
    # Iterate over the arcs in the queue
    while queue:
        # Pop the first arc from the queue
        x, y = queue.pop(0)
        # Attempt to revise variable x with respect to variable y
        if self.revise(x, y):
            # If a revision was made, add the arcs (z, x) for each neighbor z of x to the queue
            for z in self.crossword.neighbors(x):
                if z != y:
                    queue.append((z, x))
    
    # Check if any domain ended up empty
    if any(len(self.domains[var]) == 0 for var in self.crossword.variables):
        return False
    else:
        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
       return set(assignment.keys()) == set(self.crossword.variables)

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        # Check for conflicting characters
    for variable1 in assignment:
        value1 = assignment[variable1]
        # Check if the length of the assigned word is correct
        if variable1.length != len(value1):
            return False
        for variable2 in assignment:
            if variable1 != variable2:
                overlap = self.crossword.overlaps.get((variable1, variable2))
                if overlap is not None:
                    x, y = overlap
                    value2 = assignment.get(variable2)
                    if value2 is not None and value1[x] != value2[y]:
                        return False
    return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        # Get the domain of the variable var
    domain = list(self.domains[var])
    
    # Define a function to count the number of values ruled out for neighboring unassigned variables
    def count_constrained_values(value):
        constrained_values = 0
        for neighbor in self.crossword.neighbors(var):
            if neighbor not in assignment:
                for neighbor_value in self.domains[neighbor]:
                    if self.crossword.overlaps[var, neighbor] is not None:
                        x, y = self.crossword.overlaps[var, neighbor]
                        if value[x] != neighbor_value[y]:
                            constrained_values += 1
        return constrained_values
    
    # Order the domain values based on the least-constraining values heuristic
    domain.sort(key=lambda value: count_constrained_values(value))
    
    return domain

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        # Get unassigned variables
    unassigned_variables = [var for var in self.crossword.variables if var not in assignment]
    
    # Sort unassigned variables by remaining values and degree
    unassigned_variables.sort(key=lambda var: (len(self.domains[var]), -len(self.crossword.neighbors(var))))
    
    # Return the first variable from the sorted list, or None if list is empty
    return unassigned_variables[0] if unassigned_variables else None

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        # If assignment is complete, return it
    if self.assignment_complete(assignment):
        return assignment
    
    # Select an unassigned variable using minimum remaining value and degree heuristics
    var = self.select_unassigned_variable(assignment)
    
    # Iterate over the domain values of the selected variable
    for value in self.order_domain_values(var, assignment):
        # Check if the value is consistent with the current assignment
        if self.consistent(assignment):
            # Add the variable-value pair to the assignment
            assignment[var] = value
            
            # Maintain arc consistency by calling AC3
            consistent = self.ac3()
            
            # If arc consistency is maintained, recursively call backtrack with the updated assignment
            if consistent:
                result = self.backtrack(assignment)
                
                # If a complete assignment is found, return it
                if result is not None:
                    return result
                
            # If no valid assignment is found or arc consistency is not maintained, backtrack by removing the variable-value pair
            del assignment[var]
    
    # If no valid assignment is possible, return None
    return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
