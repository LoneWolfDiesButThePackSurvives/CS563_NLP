import xml.etree.ElementTree as ET

from stanza.models.constituency import tree_reader

def read_xml_file(input_filename):
    """
    Convert the CINTIL xml file to id & test

    Returns a list of tuples: (id, text)
    """
    with open(input_filename, encoding="utf-8") as fin:
        dataset = ET.parse(fin)
    dataset = dataset.getroot()
    corpus = dataset.find("{http://nlx.di.fc.ul.pt}corpus")
    if not corpus:
        raise ValueError("Unexpected dataset structure : no 'corpus'")
    trees = []
    for sentence in corpus:
        if sentence.tag != "{http://nlx.di.fc.ul.pt}sentence":
            raise ValueError("Unexpected sentence tag: {}".format(sentence.tag))
        id_node = None
        raw_node = None
        tree_nodde = None
        for node in sentence:
            if node.tag == '{http://nlx.di.fc.ul.pt}id':
                id_node = node
            elif node.tag == '{http://nlx.di.fc.ul.pt}raw':
                raw_node = node
            elif node.tag == '{http://nlx.di.fc.ul.pt}tree':
                tree_node = node
            else:
                raise ValueError("Unexpected tag in sentence {}: {}".format(sentence, node.tag))
        if id_node is None or raw_node is None or tree_node is None:
            raise ValueError("Missing node in sentence {}".format(sentence))
        tree_id = "".join(id_node.itertext())
        tree_text = "".join(tree_node.itertext())
        trees.append((tree_id, tree_text))
    return trees

def convert_cintil_treebank(input_filename, dev_size=0.1):
    """
    dev_size is the size for splitting train & dev
    """
    trees = read_xml_file(input_filename)

    test_trees = []
    train_trees = []
    for tree_id, tree_text in trees:
        if tree_text.find(" _") >= 0:
            raise ValueError("Unexpected underscore")
        tree_text = tree_text.replace("_)", ")")
        tree_text = tree_text.replace("(A (", "(A' (")
        # trees don't have ROOT, but we typically use a ROOT label at the top
        tree_text = "(ROOT %s)" % tree_text
        trees = tree_reader.read_trees(tree_text)
        if len(trees) != 1:
            raise ValueError("Unexpectedly found %d trees in %s" % (len(trees), tree_id))
        tree = trees[0]
        if tree_id.startswith("aTSTS"):
            test_trees.append(tree)
        elif tree_id.find("TSTS") >= 0:
            raise ValueError("Unexpected TSTS")
        else:
            train_trees.append(tree)

    print("Read %d test trees" % len(test_trees))
    num_train = int(len(train_trees) * (1.0 - dev_size))
    dev_trees = train_trees[num_train:]
    train_trees = train_trees[:num_train]
    print("Split %d trees into %d train and %d dev" % ((len(train_trees) + len(dev_trees)), len(train_trees), len(dev_trees)))
    return train_trees, dev_trees, test_trees


def main():
    treebank = convert_cintil_treebank("extern_data/constituency/portuguese/CINTIL/CINTIL-Treebank.xml")

if __name__ == '__main__':
    main()
