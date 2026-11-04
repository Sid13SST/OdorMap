# Example predictions

Produced by `python scripts/make_predict_examples.py`, which calls `python scripts/predict.py <SMILES>` and pastes its stdout verbatim.

**Caveat:** the model in `models/baseline_lr.joblib` is trained on **all** 4,983 molecules. For molecules that are in the dataset, these outputs show fit to training labels, not generalization. Generalization estimates are in `results/baseline.md`. Molecules marked *not in dataset* are genuinely unseen (canonical-SMILES match, stereo ignored).

## vanillin

*In training set.* Catalog descriptors: `chocolate;vanilla;creamy;sweet`

```
SMILES: COc1cc(C=O)ccc1O
 1. vanilla          1.000
 2. creamy           0.992
 3. chocolate        0.982
 4. sweet            0.969
 5. phenolic         0.967
 6. powdery          0.948
 7. spicy            0.884
 8. caramellic       0.793
 9. medicinal        0.750
10. smoky            0.712
```

## cinnamaldehyde

*In training set.* Catalog descriptors: `powdery;warm;sweet;spicy;cinnamon;aldehydic;honey;aromatic;balsamic`

```
SMILES: O=C/C=C/c1ccccc1
 1. cinnamon         1.000
 2. spicy            0.995
 3. warm             0.976
 4. balsamic         0.962
 5. aromatic         0.932
 6. powdery          0.908
 7. aldehydic        0.907
 8. honey            0.889
 9. cherry           0.873
10. sweet            0.861
```

## isoamyl acetate

*In training set.* Catalog descriptors: `fruity;ripe;sweet;solvent;pear;banana`

```
SMILES: CC(=O)OCCC(C)C
 1. banana           0.990
 2. ripe             0.954
 3. alcoholic        0.936
 4. solvent          0.926
 5. fruity           0.925
 6. pear             0.903
 7. ethereal         0.859
 8. sweet            0.857
 9. cheesy           0.847
10. pungent          0.844
```

## geraniol

*In training set.* Catalog descriptors: `fresh;natural;floral;rose;fruity;citrus;sweet;waxy`

```
SMILES: CC(C)=CCC/C(C)=C/CO
 1. citrus           0.921
 2. waxy             0.917
 3. natural          0.906
 4. fresh            0.882
 5. floral           0.852
 6. rose             0.839
 7. lily             0.814
 8. sweet            0.796
 9. muguet           0.736
10. oily             0.717
```

## limonene

*In training set.* Catalog descriptors: `fresh;phenolic;herbal;woody;citrus;orange;terpenic;lemon;sweet;pine;aromatic`

```
SMILES: CC1=CCC(CC1)C(=C)C
 1. terpenic         0.994
 2. citrus           0.988
 3. herbal           0.984
 4. lemon            0.975
 5. spicy            0.969
 6. orange           0.963
 7. pine             0.959
 8. aromatic         0.950
 9. phenolic         0.921
10. sweet            0.906
```

## dimethyl sulfide

*In training set.* Catalog descriptors: `cooked;berry;fruity;vegetable;fishy;sweet;cabbage;sulfurous;pungent;onion;green;radish;creamy;tomato`

```
SMILES: CSC
 1. sulfurous        0.985
 2. cabbage          0.973
 3. onion            0.970
 4. tomato           0.951
 5. vegetable        0.935
 6. radish           0.919
 7. fishy            0.915
 8. cooked           0.906
 9. pungent          0.901
10. garlic           0.827
```

## isovanillin

*In training set.* Catalog descriptors: `vanilla;floral;hay;herbal`

```
SMILES: O=Cc1ccc(OC)c(O)c1
 1. vanilla          1.000
 2. phenolic         0.952
 3. hay              0.950
 4. medicinal        0.939
 5. powdery          0.829
 6. spicy            0.798
 7. sweet            0.791
 8. almond           0.640
 9. herbal           0.605
10. bitter           0.523
```

## ibuprofen

*Not in dataset (unseen by the model).*

```
SMILES: CC(C)Cc1ccc(cc1)C(C)C(=O)O
 1. balsamic         0.810
 2. muguet           0.792
 3. floral           0.704
 4. oily             0.673
 5. spicy            0.614
 6. sour             0.523
 7. earthy           0.521
 8. green            0.514
 9. herbal           0.461
10. lily             0.334
```

Note: the label set has no 'odorless' class, so the model always returns some descriptors with nonzero probability, even for molecules (such as ibuprofen) that are not regarded as odorants.
