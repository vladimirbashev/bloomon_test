import getopt
import re
import sys
from abc import ABC

BOUQUET_REGEX = r'^([A-Z])([LS])(\w+[a-z])(\d+)$'
FLOWER_REGEX = r'(\d+)([a-z])'


class Flower(ABC):
    def __init__(self, specie, design_quantity=0, quantity=0):
        self.specie = specie
        self.weight = 0
        self.design_quantity = int(design_quantity)
        self.quantity = int(quantity)

    @property
    def design(self):
        return self.design_quantity > 0

    @property
    def required_quantity(self):
        result = self.design_quantity - self.quantity
        return result if result > 0 else 0

    def __str__(self):
        return str.format('{}{}', self.quantity, self.specie)


class BouquetFlower(Flower):
    def __init__(self, design_quantity, specie):
        super(BouquetFlower, self).__init__(specie, design_quantity=design_quantity)


class ExtraFlower(Flower):
    def __init__(self, quantity, specie):
        super(ExtraFlower, self).__init__(specie, quantity=quantity)


class Bouquet:
    def __init__(self, val):
        self.active = True
        self.bouquet_design = val
        groups = re.findall(BOUQUET_REGEX, val)
        if groups:
            self.name, self.size, flowers, self.total = groups[0]
            self.total = int(self.total)
            self.flowers = list(map(lambda f: BouquetFlower(*f),
                                    re.findall(FLOWER_REGEX, flowers)))

    @property
    def completed(self):
        return self.extra_flowers_quantity == 0

    @property
    def extra_flowers_quantity(self):
        return self.total - sum(f.quantity for f in self.flowers)

    def add_extra_flower(self, quantity, specie):
        fl = next((fl for fl in self.flowers if fl.specie == specie), None)
        if fl:
            fl.quantity = fl.quantity + quantity
        else:
            self.flowers.append(ExtraFlower(quantity, specie))

    def __str__(self):
        return str.format('{}{}{}',
                          self.name,
                          self.size,
                          ''.join(map(lambda f: str(f), sorted(self.flowers, key=lambda f: f.specie))))


class Parser:
    def __init__(self):
        self.flowers = dict()
        self.bouquets = list()
        self.total_flowers = {
                'L': 0,
                'S': 0
            }

    @staticmethod
    def _get_weight(total, quantity):
        return 1 - (total - quantity) / total

    def parse(self, file_name):
        def _parse_bouquet_design(line):
            self.bouquets.append(Bouquet(line))

        def _parse_flower(line):
            if line[0] not in self.flowers.keys():
                self.flowers[line[0]] = {
                    'L': 0,
                    'S': 0
                }
            self.flowers[line[0]][line[1]] += 1
            self.total_flowers[line[1]] += 1
        handler = _parse_bouquet_design
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
                handler = _parse_flower
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

    def sort_bouquets(self):
        for bd in self.bouquets:
            if bd.total > self.total_flowers[bd.size]:
                bd.active = False
            else:
                for f in bd.flowers:
                    if f.design_quantity > self._get_flowers_quantity(f.specie, bd.size):
                        bd.active = False
                        break
                    f.weight = self._get_weight(self._get_flowers_quantity(f.specie, bd.size), f.design_quantity)
            if bd.active:
                bd.weight = sum(f.weight for f in bd.flowers if f.design) + \
                            self._get_weight(self.total_flowers[bd.size], bd.total)
            else:
                bd.weight = 0

        self.bouquets.sort(key=lambda b: b.weight, reverse=True)

    def construct_bouquets(self):
        while True:
            self._fill_required_flowers()
            self._fill_extra_flowers()
            b = next((b for b in self.bouquets if not b.completed and b.active), None)
            if not b:
                break
            else:
                self._unreserve_flowers(b)
                b.active = False

    def _fill_required_flowers(self):
        for bd in self.bouquets:
            if not bd.active:
                continue
            for fl in bd.flowers:
                if not self._reserve_flower(fl, bd):
                    self._unreserve_flowers(bd)
                    break

    def _fill_extra_flowers(self):
        for bd in self.bouquets:
            if bd.completed:
                continue
            for fl in bd.flowers:
                self._add_extra_flower(bd, fl.specie)
                if bd.completed:
                    break
            if bd.completed:
                continue
            for specie in list(self.flowers.keys()):
                self._add_extra_flower(bd, specie)
                if bd.completed:
                    break

    def _add_extra_flower(self, bouquet, specie):
        quantity = self._get_flowers_quantity(specie, bouquet.size)
        if quantity <= 0:
            return False
        if quantity >= bouquet.extra_flowers_quantity:
            quantity = bouquet.extra_flowers_quantity
        bouquet.add_extra_flower(quantity, specie)
        self.flowers[specie][bouquet.size] = self.flowers[specie][bouquet.size] - quantity
        return True

    def _unreserve_flowers(self, bouquet):
        for fl in bouquet.flowers:
            if fl.quantity:
                self.flowers[fl.specie][bouquet.size] = self.flowers[fl.specie][bouquet.size] + fl.quantity
        bouquet.flowers = [fl for fl in bouquet.flowers if fl.quantity > 0 or fl.design]

    def _reserve_flower(self, flower, bouquet):
        if flower.required_quantity == 0:
            return True
        elif flower.required_quantity <= self._get_flowers_quantity(flower.specie, bouquet.size):
            rq = flower.required_quantity
            flower.quantity = flower.quantity + rq
            self.flowers[flower.specie][bouquet.size] = self.flowers[flower.specie][bouquet.size] - rq
            return True
        else:
            return False

    def _get_flowers_quantity(self, specie, size):
        if specie in self.flowers.keys() and size in self.flowers[specie].keys():
            return self.flowers[specie][size]
        else:
            return 0


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
        print(str.format('Parsing file {}', input_file))
        p.parse(input_file)
        print('Sort bouquets')
        p.sort_bouquets()
        print('Construct bouquets')
        p.construct_bouquets()
        print(str.format('Saving to file {}', output_file))
        p.save(output_file)


if __name__ == '__main__':
    main(sys.argv[1:])
