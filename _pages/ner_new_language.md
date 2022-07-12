---
layout: page
title: Adding a new NER model
keywords: ner, named entity recognition, stanza, model training
permalink: '/ner_new_language.html'
nav_order: 7
parent: Usage
---

## End to End NER example

Here is a complete end to end example on how to build an NER model for a previously unknown language.  For this example, we will use a Bengali dataset:

[data](https://github.com/Rifat1493/Bengali-NER)

[publication](https://ieeexplore.ieee.org/document/8944804)

### OS

We will work on Linux for this.  It is possible to recreate most of
these steps on Windows or another OS, with the exception that the
environment variables need to be set differently.

As a reminder, Stanza only supports Python 3.6 or later.
If you are using an earlier version of Python, it will not work.

### Codebase

This is a previously unknown dataset, so it will require some code
changes.  Accordingly, we first clone
[the stanza git repo](https://github.com/stanfordnlp/stanza)
and check out the `dev` branch.  We will then create a new branch
for our code changes.

```bash
git clone git@github.com:stanfordnlp/stanza.git
cd stanza
git checkout dev
git checkout -b bangla_ner
```

### Environment

There are many environment variables mentioned in the usage page,
along with a `config.sh` script which can set them up.  However,
ultimately only two are relevant for an NER model, `$NERBASE` and
`$NER_DATA_DIR`.

Both of these have reasonable defaults, but we can still customize them.

`$NERBASE` determines where the *raw, unchanged* datasets go.

The purpose of the data preparation scripts will be to put *processed*
forms of this data in `$NER_DATA_DIR`.  Once this is done, the
execution script will expect to find the data in that directory.

In `~/.bashrc`, we can add the following lines.  Here are a couple
values we use on our cluster to organize shared data:

```bash
export NERBASE=/u/nlp/data/ner/stanza
export NER_DATA_DIR=/nlp/scr/$USER/data/ner
```

Since you will be running python programs directly from the git checkout of Stanza, you will need to make sure `.` is in your `PYTHONPATH`.

```bash
echo $PYTHONPATH
```

If you have a blank `PYTHONPATH`, or your path does not include `.`, please also add this to your startup script:

```bash
export PYTHONPATH=$PYTHONPATH:.
```

### Data download

We can organize the data in a variety of ways.  For this dataset, we
will choose to organize it in a directory for `bangla`, since there
are many datasets and we need to keep the data directory
understandable.

```bash
cd $NERBASE
mkdir -p bangla
cd bangla
git clone git@github.com:Rifat1493/Bengali-NER.git
```

### Processing raw data to .json

The NER model takes as input a `.json` format which separates words
and labels.  This can be inconvenient to write, though, so the easiest
thing to do is to start with a
[`BIO`](https://en.wikipedia.org/wiki/Inside–outside–beginning_(tagging))
file and convert it using an existing bio->json function we provide.

The data in this dataset is already in TSV format, pretty close to the
BIO format, but there are a couple issues:

- Some of the data lines in the train set have no text, but still have a label of `O`
- The data is in two files, train and test, whereas we need a dev file for validation.
- The `TIM` tag does not have `B-` or `I-` labels.

To address these issues, we wrote a small conversion script.  First, we decide on a
"short name" for the dataset.  The language code for Bangla is `bn`, and the
authors of this dataset are all at Daffodil University, so we choose `bn_daffodil`.

Next, we write a short script which does each of these things.  Our
conversion script adjusts all of the tags so they fit a `B-TAG`,
`I-TAG`, `E-TAG` scheme and randomly splits the training data into
train & dev sets.  We set a random seed for the random split so that
the split is repeatable.  Note that not all of these changes are
always necessary for different datasets.  All that is necessary is for
the script to turn the raw input into BIO format, at which point you
can call the function to translate it into `.json`

We will call this script

```
stanza/utils/datasets/ner/convert_bn_daffodil.py
```

In `stanza/utils/datasets/ner/prepare_ner_dataset.py`, we add the following stub
(note the reuse of the directory structure we created above):

```python
def process_bn_daffodil(paths, short_name):
    in_directory = os.path.join(paths["NERBASE"], "bangla", "Bengali-NER")
    out_directory = paths["NER_DATA_DIR"]
    convert_bn_daffodil.convert_dataset(in_directory, out_directory)
```

We add a mapping in the `DATASET_MAPPING` and a bit of documentation
regarding the dataset, and we now have a script which will prepare the
Daffodil dataset for use as a Bangla NER dataset.

[This is the complete change described here.](https://github.com/stanfordnlp/stanza/commit/1ad08b4f07f24eff01e2f9949fcf7f63226e154d)

### Word Vectors

This is not everything we need, though, as this is the first model we
have created for Bangla in Stanza.  We also need to obtain pretrained
word embeddings for this language or any other new language we add.

{% include alerts.html %}
{{ note }}
{{ "If a language is already in Stanza, this step is not necessary." | markdownify }}
{{ end }}

For Bangla word vectors, we found
[Fasttext vectors](https://fasttext.cc/docs/en/crawl-vectors.html).
We download the text file for this language.  There are probably other
sources we can choose from if we take some time to search.

Once these are downloaded, there is a `convert_pretrain.py` script
which turns the raw text file (or a .gz file, for example) into a
`.pt` file such as what Stanza uses.

```bash
# be sure to update the language abbreviation "bn" to match your dataset!
# 150000 is usually a good balance between good coverage and a model which is too large
python3 stanza/models/common/convert_pretrain.py ~/stanza_resources/bn/pretrain/fasttext.pt ~/extern_data/wordvec/fasttext/cc.bn.300.vec.gz 150000
```

Note that by default, Stanza will keep its resources in the
`~/stanza_resources` directory.  This can be updated by changing the
`$STANZA_RESOURCES_DIR` environment variable.

### Training!

At this point, everything is ready to push the button and start training.

```bash
python -m stanza.utils.training.run_ner bn_daffodil
```

This will create a model which goes in `saved_models/ner/bn_daffodil_nertagger.pt`

You can get the dev & test scores on your dataset for this model with

```bash
python -m stanza.utils.training.run_ner bn_daffodil --score_dev
python -m stanza.utils.training.run_ner bn_daffodil --score_test
```

### Charlm and Bert

The model produced by the above script is actually not that great on
this dataset.  It can be improved by adding a character language
model, which is quite cheap but takes a long time to train, or by
adding a Bert model or other transformer.

Creating a new [charlm](new_language.md#character-lm) can make a
substantial improvement to the results, but will take a few days to
train.

First, we need a large amount of text data.  For this model, we choose
two sources: Oscar Common Crawl and Wikipedia.

There is a script to copy Oscar from HuggingFace:

```bash
python3 -m stanza.utils.charlm.dump_oscar bn --output /nlp/scr/horatio/oscar/
```

{% include alerts.html %}
{{ note }}
{{ "To use this script, you will need to install the HuggingFace library `datasets`." | markdownify }}
{{ end }}

We also download Wikipedia from the
[Wikipedia dumps archive](https://dumps.wikimedia.org/backup-index-bydb.html).
If a dump exists for your language, it will be under the language code
for that language.
We will use Prof. Attardi's
[WikiExtractor](https://github.com/attardi/wikiextractor) tool to
remove the markup, and it works on the `latest-pages-meta-current`
file, so that is what we download.

```bash
wget https://dumps.wikimedia.org/bnwiki/latest/bnwiki-latest-pages-meta-current.xml.bz2
```

You can then use the WikiExtractor to extract the text from the
Wikipedia dump you just downloaded:

```bash
python -m wikiextractor.WikiExtractor bnwiki-latest-pages-meta-current.xml.bz2
```

This splits the text into multiple subdirectories full of small files
`AA, AB, ...` depending on the size.  The splits are smaller than we
need, but we can combine them:

```bash
for i in `ls text`; do echo $i; cat text/$i/* > $i.txt; xz $i.txt; done
```

We now have an Oscar dump and a Wikipedia dump.  We can turn this raw
data into train/dev/test splits for the charlm.  First, we organize
the raw data into one directory.  Then, we run the `make_lm_data` script.
On our cluster, we put all of our raw charlm data into
`/u/nlp/software/stanza/charlm_raw`
and the train/dev/test splits into `/u/nlp/software/stanza/charlm`
You can choose different base paths, of course.

```bash
export CHARLM_DIR=/u/nlp/software/stanza/charlm
export CHARLM_RAW_DIR=/u/nlp/software/stanza/charlm_raw
# move the Oscar & Wikipedia .xz files to this directory
mkdir -p $CHARLM_RAW_DIR/bn/oscar

ls $CHARLM_RAW_DIR/bn/oscar
AA.txt.xz  oscar_dump_000.txt.xz  oscar_dump_007.txt.xz  oscar_dump_014.txt.xz  oscar_dump_021.txt.xz
AB.txt.xz  oscar_dump_001.txt.xz  oscar_dump_008.txt.xz  oscar_dump_015.txt.xz  oscar_dump_022.txt.xz
AC.txt.xz  oscar_dump_002.txt.xz  oscar_dump_009.txt.xz  oscar_dump_016.txt.xz  oscar_dump_023.txt.xz
AD.txt.xz  oscar_dump_003.txt.xz  oscar_dump_010.txt.xz  oscar_dump_017.txt.xz
AE.txt.xz  oscar_dump_004.txt.xz  oscar_dump_011.txt.xz  oscar_dump_018.txt.xz
AF.txt.xz  oscar_dump_005.txt.xz  oscar_dump_012.txt.xz  oscar_dump_019.txt.xz
AG.txt.xz  oscar_dump_006.txt.xz  oscar_dump_013.txt.xz  oscar_dump_020.txt.xz

python3 -m stanza.utils.charlm.make_lm_data $CHARLM_RAW_DIR $CHARLM_DIR --langs bn --packages oscar
```

{% include alerts.html %}
{{ note }}
{{ "make_lm_data has several subprocess calls which are not expected to work on Windows." | markdownify }}
{{ end }}

{% include alerts.html %}
{{ note }}
{{ "Please double check that the directory with the data is `$CHARLM_RAW_DIR/<lang>/<dataset>`" | markdownify }}
{{ end }}

You can now run the charlm.  This will take days.  Remember to update the language!

```bash
python3 -m stanza.models.charlm --train_dir $CHARLM_DIR/bn/oscar/train --eval_file $CHARLM_DIR/bn/oscar/dev.txt.xz --direction forward --lang bn --shorthand bn_oscar --mode train > bn_forward.out 2>&1 &
python3 -m stanza.models.charlm --train_dir $CHARLM_DIR/bn/oscar/train --eval_file $CHARLM_DIR/bn/oscar/dev.txt.xz --direction backward --lang bn --shorthand bn_oscar --mode train > bn_backward.out 2>&1 &
```

You can tell when the model has converged and is no longer improving by looking for the eval scores:

```bash
grep "eval checkpoint" bn_*.out
```

Alternatively, you can tie it in to wandb (requires Stanza 1.4.1 or later) by signing in to wandb and adding `wandb_name` to the original command line:

```bash
python3 -m stanza.models.charlm --train_dir $CHARLM_DIR/bn/oscar/train --eval_file $CHARLM_DIR/bn/oscar/dev.txt.xz --direction forward --lang bn --shorthand bn_oscar --mode train --wandb_name bn_oscar_forward_charlm > bn_forward.out 2>&1 &
python3 -m stanza.models.charlm --train_dir $CHARLM_DIR/bn/oscar/train --eval_file $CHARLM_DIR/bn/oscar/dev.txt.xz --direction backward --lang bn --shorthand bn_oscar --mode train --wandb_name bn_oscar_backward_charlm > bn_backward.out 2>&1 &
```

Once it has converged satisfactorily, you can copy the models to the
expected locations in your stanza resources and rerun the NER.  If you
follow the name structure used in this example command line,
`run_ner.py` will look for and find the charlm in these exact paths.
Remember that you can update $STANZA_RESOURCES_DIR if you need.

```bash
mkdir -p ~/stanza_resources/bn/forward_charlm
cp saved_models/charlm/bn_oscar_forward_charlm.pt ~/stanza_resources/bn/forward_charlm/oscar.pt

mkdir -p ~/stanza_resources/bn/backward_charlm
cp saved_models/charlm/bn_oscar_backward_charlm.pt ~/stanza_resources/bn/backward_charlm/oscar.pt

python3 -m stanza.utils.training.run_ner bn_daffodil --charlm oscar --save_name bn_daffodil_charlm.pt
```

You can choose a Transformer module from HuggingFace and then use it as follows:


```bash
python -m stanza.utils.training.run_ner bn_daffodil --bert_model sagorsarker/bangla-bert-base --save_name bn_daffodil_bert.pt
```

If the Transformer helps (as expected), you can add it to the map in `stanza/utils/training/common.py`.

{% include alerts.html %}
{{ note }}
{{ "Not all HF Transformer models are integrated with our code yet.  If you encounter such a model, please let us know." }}
{{ end }}

### Training multiple models

Note that if you are attempting to train a new model, the `run`
scripts will not clobber an existing model.  There are two ways to
work around that:

```bash
# --save_name will give the script a new model name to save
# using the new name will keep both the old and new models
python -m stanza.utils.training.run_ner bn_daffodil --bert_model sagorsarker/bangla-bert-base --save_name bn_daffodil_bert.pt

# --force will overwrite the old model with a new model
# kiss the old model goodbye
python -m stanza.utils.training.run_ner bn_daffodil --bert_model sagorsarker/bangla-bert-base --force
```

### Contributing back

If you like, you can open a PR with your code changes and post the
models somewhere we can integrate them.  It would be very appreciated!
