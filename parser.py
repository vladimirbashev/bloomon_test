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
        groups = re.findall(BOUQUET_REGEX, val)
        if groups:
            self.name, self.size, flowers, self.total = groups[0]
            self.total = int(self.total)
            self.flowers = list(map(lambda f: Flower(*f, design=True, reserved=False),
                                    re.findall(FLOWER_REGEX, flowers)))
            self.has_extra_flowers = self.total > sum(f.quantity for f in self.flowers)

    @property
    def quantity(self):
        return sum(f.quantity for f in self.flowers if f.reserved)

    @property
    def completed(self):
        return self.difference == 0

    @property
    def difference(self):
        return self.total - self.quantity

    def add_extra_flower(self, quantity, specie):
        fl = next((fl for fl in self.flowers if fl.specie == specie), None)
        if fl:
            fl.quantity = fl.quantity + quantity
        else:
            self.flowers.append(Flower(quantity, specie))

    def __str__(self):
        return str.format('{}{}{}',
                          self.name,
                          self.size,
                          ''.join(map(lambda f: str(f), sorted(self.flowers, key=lambda f: f.specie))))


class Parser:
    def __init__(self):
        self.flowers = dict()
        self.bouquets = list()

    def construct(self):
        self._fill_required_flowers()
        self._fill_extra_flowers()

    def parse(self, file_name):
        handler = self._parse_bouquet_design
        try:
            file = open(file_name, "r")
        except FileNotFoundError:
            print(str.format('File {} not found', file_name))
            raise

        while True:
            line = file.readline()
            if not line:
                break
            if line == "\n":
                handler = self._parse_flower
            else:
                handler(line)

        file.close()

    def save(self, file_name):
        try:
            file = open(file_name, 'w')
        except FileNotFoundError:
            print(str.format('Cannot save file {}', file_name))
            raise
        for bd in self.bouquets:
            if bd.completed:
                file.write(str(bd))
                file.write('\n')
        file.close()

    def _parse_bouquet_design(self, line):
        self.bouquets.append(Bouquet(line))

    def _parse_flower(self, line):
        if line[0] not in self.flowers.keys():
            self.flowers[line[0]] = {
                'L': 0,
                'S': 0
            }
        self.flowers[line[0]][line[1]] += 1

    def _find_specie(self, quantity, size):
        return next((k for k, v in self.flowers.items() if v[size] >= quantity), None)

    def _get_flowers_quantity(self, specie, size):
        if specie in self.flowers.keys() and size in self.flowers[specie].keys():
            return self.flowers[specie][size]
        else:
            return 0

    def _add_extra_flower(self, bouquet, quantity, specie):
        bouquet.add_extra_flower(quantity, specie)
        self.flowers[specie][bouquet.size] = self.flowers[specie][bouquet.size] - quantity

    def _reserve_flower(self, flower, bouquet):
        if flower.reserved:
            return True
        elif flower.quantity <= self._get_flowers_quantity(flower.specie, bouquet.size):
            flower.reserved = True
            self.flowers[flower.specie][bouquet.size] = self.flowers[flower.specie][bouquet.size] - flower.quantity
            return True
        else:
            return False

    def _unreserve(self, bouquet):
        for fl in bouquet.flowers:
            if fl.reserved:
                fl.reserved = False
                self.flowers[fl.specie][bouquet.size] = self.flowers[fl.specie][bouquet.size] + fl.quantity
            bouquet.flowers = [fl for fl in bouquet.flowers if not fl.reserved and not fl.design]

    def _fill_required_flowers(self):
        for bd in self.bouquets:
            for fl in bd.flowers:
                if not self._reserve_flower(fl, bd):
                    self._unreserve(bd)
                    break

    def _fill_extra_flowers(self):
        for bd in self.bouquets:
            if not bd.has_extra_flowers:
                continue
            quantity = bd.difference
            if quantity > 0:
                specie = self._find_specie(quantity, bd.size)
                if specie:
                    self._add_extra_flower(bd, quantity, specie)
                else:
                    self._unreserve(bd)


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
            print('parser.py -i <inputfile> -o <outputfile>')
            sys.exit()
        elif opt in ('-i', '--ifile'):
            input_file = arg
        elif opt in ('-o', '--ofile'):
            output_file = arg

    if not input_file:
        print('Please specify input file name: -i <inputfile>.')
    elif not output_file:
        print('Please specify output file name: -0 <outputfile>.')
    else:
        print('Parser is run.')
        p = Parser()
        print(str.format('Parsing {}', input_file))
        p.parse(input_file)
        print('Construct bouquets')
        p.construct()
        print(str.format('Saving to {}', output_file))
        p.save(output_file)


if __name__ == '__main__':
    main(sys.argv[1:])

