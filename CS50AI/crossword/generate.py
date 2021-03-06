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
                        w, h = draw.textsize(letters[i][j], font=font)
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
        
        for var in self.domains:
            node_consistent = self.domains[var].copy()
            for word in self.domains[var]:
                if len(word) != var.length:
                    node_consistent.remove(word)
            self.domains[var] = node_consistent

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.
        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """

        revised = False
        overlap = self.crossword.overlaps[x,y]
        xDomCpy = self.domains[x].copy()

        for x_word in self.domains[x]:
            options = 0
            for y_word in self.domains[y]:
                if x_word[overlap[0]] == y_word[overlap[1]] and x_word != y_word:
                    options += 1
            if options == 0:
                xDomCpy.remove(x_word)
                revised = True
        
        self.domains[x] = xDomCpy

        return revised

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.
        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """

        if arcs == None:
            arcs = []
            for x in self.domains:
                for y in self.crossword.neighbors(x):
                    arc = (x, y)
                    arcs.append(arc)

        while len(arcs) > 0:
            arc = arcs.pop()
            x = arc[0]
            y = arc[1]

            if self.revise(x, y):
                if len(self.domains[x]) == 0:
                    return False

                x_neighbours_no_y = self.crossword.neighbors(x)
                x_neighbours_no_y.remove(y)
                
                for z in x_neighbours_no_y:
                    arc = (z, x)
                    arcs.append(arc)

        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """

        for var in assignment:
            if assignment[var] == None:
                return False
        return True

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """

        for x in assignment:
            if assignment[x] == None:
                continue
            else:
                for y in self.crossword.neighbors(x):
                    if assignment[y] == None:
                        continue
                    else:
                        overlap = self.crossword.overlaps[x,y]
                        x_word = assignment[x]
                        y_word = assignment[y]

                        if x_word[overlap[0]] != y_word[overlap[1]] or x_word == y_word:
                            return False
        
        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """

        sorted_domain_dict = {
            word: 0
            for word in self.domains[var]
        }

        for word in self.domains[var]:
            options_removed = 0
            for var_neighbour in self.crossword.neighbors(var):
                overlap = self.crossword.overlaps[var,var_neighbour]
                for word_neighbour in self.domains[var_neighbour]:
                    if word[overlap[0]] != word_neighbour[overlap[1]] or word == word_neighbour:
                        options_removed += 1
            sorted_domain_dict[word] = options_removed
                
        sorted_domain_dict = {k: v for k, v in sorted(sorted_domain_dict.items(), key=lambda item: item[1])}
        sorted_domain_list = []
        for word in sorted_domain_dict:
            sorted_domain_list.append(word)
        
        return sorted_domain_list

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """

        min_dom_vals = float("inf")

        for var in assignment:
            if assignment[var] == None:
                if len(self.domains[var]) < min_dom_vals:
                    min_dom_vals = len(self.domains[var])
                    selected_var = var
                elif len(self.domains[var]) == min_dom_vals:
                    if len(self.crossword.neighbors(var)) > len(self.crossword.neighbors(selected_var)):
                        min_dom_vals = len(self.domains[var])
                        selected_var = var

        return selected_var

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.
        `assignment` is a mapping from variables (keys) to words (values).
        If no assignment is possible, return None.
        """


        if assignment == dict():
            assignment = {
                var: None
                for var in self.crossword.variables
            }
            for var in assignment:
                if len(self.domains[var]) == 1:
                    assignment[var] = self.domains[var].pop()

        if self.assignment_complete(assignment):
            return assignment

        var = self.select_unassigned_variable(assignment)

        for value in self.order_domain_values(var, assignment):
            temp_assignment = assignment.copy()
            temp_assignment[var] = value

            if self.consistent(temp_assignment):
                assignment[var] = value

                arcs = []
                for y in self.crossword.neighbors(var):
                    arc = (y, var)
                    arcs.append(arc)
                
                inferences = self.ac3(arcs)

                if inferences == True:
                    for var_chk in assignment:
                        if assignment[var_chk] == None and len(self.domains[var_chk]) == 1:
                            assignment[var_chk] = self.domains[var_chk].pop()

                result = self.backtrack(assignment)

                if result != None:
                    return result

            self.domains[var].remove(value)

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
