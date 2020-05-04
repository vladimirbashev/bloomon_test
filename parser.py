import click
import re
from abc import ABC

BOUQUET_REGEX = r'^([A-Z])([LS])(\w+[a-z])(\d+)$'
FLOWER_REGEX = r'(\d+)([a-z])'


class Flower(ABC):
    """An abstract class for a flower"""

    def __init__(self, specie, design_quantity=0, quantity=0):
        self.specie = specie
        self.weight = 0
        self.design_quantity = int(design_quantity)  # number of a flower in bouquet design
        self.quantity = int(quantity)  # actual number of flowers in bouquet

    @property
    def design(self):
        """Check if a flower is a part of design"""
        return self.design_quantity > 0

    @property
    def required_quantity(self):
        """Checked how many extra flowers needs to be added to complete a bouquet"""
        result = self.design_quantity - self.quantity
        return result if result > 0 else 0

    def __str__(self):
        """Represents string value of a flower"""
        return str.format('{}{}', self.quantity, self.specie)


class BouquetFlower(Flower):
    """Created a flower. A bouquet flower means design_quantity>0"""

    def __init__(self, design_quantity, specie):
        super(BouquetFlower, self).__init__(specie, design_quantity=design_quantity)


class ExtraFlower(Flower):
    """Created a flower. An extra flower means design_quantity=0"""

    def __init__(self, quantity, specie):
        super(ExtraFlower, self).__init__(specie, quantity=quantity)


class Bouquet:
    """Creates a bouquet design, also used to construct bouquets"""

    def __init__(self, val):
        self.active = True  # bouquet is deactivated if cannot be completed
        self.bouquet_design = val
        groups = re.findall(BOUQUET_REGEX, val)
        if groups:
            self.name, self.size, flowers, self.total = groups[0]
            self.total = int(self.total)
            self.flowers = list(map(lambda f: BouquetFlower(*f), re.findall(FLOWER_REGEX, flowers)))

    @property
    def completed(self):
        """Check if a bouquet is completed"""
        return self.design_completed and sum(f.quantity for f in self.flowers) == self.total

    @property
    def design_completed(self):
        """Check if a bouquet has all needed design flowers"""
        return all(f.design_quantity <= f.quantity for f in self.flowers)

    @property
    def extra_flowers_quantity(self):
        """Checks how many extra flowers need to be added to complete a bouquet"""
        return self.total - sum(f.design_quantity for f in self.flowers)

    def add_extra_flower(self, quantity, specie):
        """Adds an extra flowers to a bouquet"""
        fl = next((fl for fl in self.flowers if fl.specie == specie), None)
        if fl:
            fl.quantity = fl.quantity + quantity
        else:
            self.flowers.append(ExtraFlower(quantity, specie))

    def __str__(self):
        """Represents string value of bouquet"""
        return str.format('{}{}{}',
                          self.name,
                          self.size,
                          ''.join(map(lambda f: str(f), sorted(self.flowers, key=lambda f: f.specie))))


class Parser:
    """Class implements logic for bouquets construction."""

    def __init__(self):
        self.flowers = dict()  # available flowers
        self.bouquets = list()  # bouquet designs
        self.total_flowers = {  # total available flowers, user to calculates weights
            'L': 0,
            'S': 0
        }

    @staticmethod
    def _get_weight(total, quantity):
        """Calculates weight of a flower"""
        return 1 - (total - quantity) / total

    def _fill_test_data(self):
        """Prepares test data"""
        self._parse_bouquet_design('AL10a15b5c30')
        self._parse_bouquet_design('AS10a10b25')
        self._parse_bouquet_design('BL15b1c21')
        self._parse_bouquet_design('BS10b5c16')
        self._parse_bouquet_design('CL20a15c45')
        self._parse_bouquet_design('DL20b28')
        for i in range(10):
            self._parse_flower('aL')
            self._parse_flower('bL')
            self._parse_flower('cL')
            self._parse_flower('aS')
            self._parse_flower('bS')
            self._parse_flower('cS')

    def _parse_bouquet_design(self, line):
        """Serialize string value into a bouquet object"""
        self.bouquets.append(Bouquet(line))

    def _parse_flower(self, line):
        """Serialize string value into a flower object"""
        if line[0] not in self.flowers.keys():
            self.flowers[line[0]] = {
                'L': 0,
                'S': 0
            }
        self.flowers[line[0]][line[1]] += 1
        self.total_flowers[line[1]] += 1

    def parse(self, is_test):
        """Method implements data input or test data usage(based on input parameter).
        Data is stored on self.flowers and self.bouquets structures."""
        if is_test:
            self._fill_test_data()
        else:
            print('Please enter bouquet designs:')
            while True:
                line = input()
                if line:
                    self._parse_bouquet_design(line)
                else:
                    break

            print('Please enter flowers:')
            while True:
                line = input()
                if line:
                    self._parse_flower(line)
                else:
                    break

    def print(self):
        """Prints completed bouquets"""
        print('\nResult:')
        for bd in self.bouquets:
            if bd.completed:
                print(str(bd))

    def sort_bouquets(self):
        """Method sorts bouquet designs based on bouquets weight.
        Weights reflects bouquet complexity, in other words big bouquets with rare flowers should be prepared first."""
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
        """Method constructs bouquets based on designs.
        It is done in infinite loop. A one uncompleted bouquet is excluded from logic on each loop
        to free flowers for other uncompleted bouquets"""
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
        """Adds design flowers to bouquets"""
        for bd in self.bouquets:
            if not bd.active or bd.completed or bd.design_completed:
                continue
            for fl in bd.flowers:
                if not self._add_required_flower(fl, bd):
                    self._unreserve_flowers(bd)
                    break

    def _fill_extra_flowers(self):
        """Adds non design flowers to bouquets"""
        for bd in self.bouquets:
            if bd.completed or not bd.active or not bd.design_completed:
                continue
            for fl in bd.flowers:
                self._add_extra_flower(bd, fl.specie)
                if bd.completed:
                    break
            if bd.completed:
                continue
            for specie in self.flowers:
                self._add_extra_flower(bd, specie)
                if bd.completed:
                    break

    def _add_extra_flower(self, bouquet, specie):
        """Add a non design flower to a bouquet"""
        quantity = self._get_flowers_quantity(specie, bouquet.size)
        if quantity <= 0:
            return False
        if quantity >= bouquet.extra_flowers_quantity:
            quantity = bouquet.extra_flowers_quantity
        bouquet.add_extra_flower(quantity, specie)
        self.flowers[specie][bouquet.size] = self.flowers[specie][bouquet.size] - quantity
        return True

    def _add_required_flower(self, flower, bouquet):
        """Add a design flowers to a bouquet"""
        if flower.required_quantity == 0:
            return True
        elif flower.required_quantity <= self._get_flowers_quantity(flower.specie, bouquet.size):
            rq = flower.required_quantity
            flower.quantity = flower.quantity + rq
            self.flowers[flower.specie][bouquet.size] = self.flowers[flower.specie][bouquet.size] - rq
            return True
        else:
            return False

    def _unreserve_flowers(self, bouquet):
        """Removes flowers from a bouquet and adds flowers to available flowers"""
        for fl in bouquet.flowers:
            if fl.quantity:
                self.flowers[fl.specie][bouquet.size] = self.flowers[fl.specie][bouquet.size] + fl.quantity
        bouquet.flowers = [fl for fl in bouquet.flowers if fl.quantity > 0 or fl.design]

    def _get_flowers_quantity(self, specie, size):
        """Returns available number of flowers with provided specie and size"""
        if specie in self.flowers.keys() and size in self.flowers[specie].keys():
            return self.flowers[specie][size]
        else:
            return 0


@click.command()
@click.option('--test', default='n', help='Using test data')
def main(test):
    p = Parser()
    p.parse(test.lower() == 'y')
    p.sort_bouquets()
    p.construct_bouquets()
    p.print()


if __name__ == '__main__':
    main()
