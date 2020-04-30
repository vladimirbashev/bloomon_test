import getopt
import re
import sys

BOUQUET_REGEX = r'^([A-Z])([LS])(\w+[a-z])(\d+)$'
FLOWER_REGEX = r'(\d+)([a-z])'


class Flower:
    def __init__(self, quantity, specie, design=False, reserved=True):
        self.quantity = int(quantity)
        self.specie = specie
        self.reserved = reserved
        self.design = design

    def __str__(self):
        return str.format('{}{}', self.quantity, self.specie)


class Bouquet:
    def __init__(self, val):
        self.bouquet_design = val
        bgroups = re.findall(BOUQUET_REGEX, val)
        if bgroups:
            self.name, self.size, flowers, self.total = bgroups[0]
            self.total = int(self.total)
            self.flowers = list(map(lambda f: Flower(*f, design=True, reserved=False),
                                    re.findall(FLOWER_REGEX, flowers)))

    def get_quantity(self):
        return sum(f.quantity for f in self.flowers)

    def completed(self):
        return self.get_difference() == 0

    def get_difference(self):
        return self.total - self.get_quantity()

    def __str__(self):
        return str.format('{}{}{}',
                          self.name,
                          self.size,
                          ''.join(map(lambda f: str(f), sorted(self.flowers, key=lambda f: f.specie))))


class Parser:
    def __init__(self):
        self.flowers = dict()
        self.bouquet_designs = list()

    def _parse_bouquet_design(self, line):
        self.bouquet_designs.append(Bouquet(line))

    def _parse_flower(self, line):
        if line[0] not in self.flowers.keys():
            self.flowers[line[0]] = {
                'L': 0,
                'S': 0
            }
        self.flowers[line[0]][line[1]] += 1

    def parse(self, file_name):
        handler = self._parse_bouquet_design
        try:
            file = open(file_name, "r")
        except FileNotFoundError:
            print(str.format('File {} not found', file_name))
            raise

        while True:
            # Get next line from file
            line = file.readline()
            # If line is empty then end of file reached
            if not line:
                break
            if line == "\n":
                handler = self._parse_flower
            else:
                handler(line)

        # Close Close
        file.close()

    def _find_specie(self, quantity, size):
        return next((k for k, v in self.flowers.items() if v[size] >= quantity), None)

    def _decrease_flowers(self, specie, size, quantity):
        self.flowers[specie][size] = self.flowers[specie][size] - quantity

    def _fill_required_flowers(self):
        not_completed_bouquets = list()
        for bd in self.bouquet_designs:
            for fl in bd.flowers:
                if fl.reserved:
                    continue
                if fl.quantity < self.flowers[fl.specie][bd.size]:
                    fl.reserved = True
                    self._decrease_flowers(fl.specie, bd.size, fl.quantity)
            if not bd.completed():
                not_completed_bouquets.append(bd)
        self._fill_extra_flowers(not_completed_bouquets)

    def _fill_extra_flowers(self, not_completed_bouquets):
        for bd in not_completed_bouquets:
            quantity = bd.get_difference()
            if quantity > 0:
                specie = self._find_specie(quantity, bd.size)
                if specie:
                    bd.flowers.append(Flower(quantity, specie))
                    self._decrease_flowers(specie, bd.size, quantity)
                else:
                    not_completed_bouquets.append(bd)
        return not_completed_bouquets

    def construct(self):
        self._fill_required_flowers()

    def save(self, file_name):
        file = open(file_name, 'w')
        for bd in self.bouquet_designs:
            file.write(str(bd))
            file.write('\n')
        file.close()


def main(argv):
    input_file = ''
    output_file = ''
    try:
        opts, args = getopt.getopt(argv, "hi:o:", ["ifile=", "ofile="])
    except getopt.GetoptError:
        print('Incorrect parameters')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('test.py -i <inputfile> -o <outputfile>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            input_file = arg
        elif opt in ("-o", "--ofile"):
            output_file = arg

    print('Parser is run.')
    p = Parser()
    print(str.format('Parsing {}', input_file))
    p.parse(input_file)
    print('Construct bouquets')
    p.construct()
    print(str.format('Saving to {}', output_file))
    p.save(output_file)


if __name__ == "__main__":
    main(sys.argv[1:])

