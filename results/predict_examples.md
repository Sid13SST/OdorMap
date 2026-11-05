# Example predictions

Produced by `python scripts/make_predict_examples.py`, which calls `python scripts/predict.py <SMILES>` and pastes its stdout verbatim.

**Caveat:** the model in `models/baseline_lr.joblib` is trained on **all** 3,522 Leffingwell molecules. For molecules that are in the dataset, these outputs show fit to training labels, not generalization. Generalization estimates are in `results/baseline.md`. Molecules marked *not in dataset* are not found in the training data (canonical-SMILES match, stereo ignored); their predictions are unvalidated, since there is no ground truth for them and close structural analogs may exist in the training set. The `Training membership` line is printed by `predict.py` itself.

Numbers are model confidence **scores**, not calibrated probabilities (see `results/calibration.md`).

## vanillin

*In training set.* Catalog descriptors (1 row(s) with this stereo-free structure): `vanillin: creamy;vanilla`

```
SMILES: COc1cc(C=O)ccc1O
Training membership: in training data (memorization possible)
Scores are model confidence, not calibrated probabilities.
 1. vanilla          0.999
 2. creamy           0.953
 3. sweet            0.884
 4. spicy            0.779
 5. smoky            0.533
 6. cinnamon         0.300
 7. phenolic         0.296
 8. balsamic         0.247
 9. floral           0.238
10. woody            0.187
```

## cinnamaldehyde

*In training set.* Catalog descriptors (1 row(s) with this stereo-free structure): `cinnamaldehyde: cinnamon;spicy`

```
SMILES: O=C/C=C/c1ccccc1
Training membership: in training data (memorization possible)
Scores are model confidence, not calibrated probabilities.
 1. cinnamon         0.999
 2. spicy            0.983
 3. balsamic         0.977
 4. warm             0.971
 5. sweet            0.695
 6. herbal           0.467
 7. vanilla          0.433
 8. almond           0.427
 9. cocoa            0.276
10. honey            0.255
```

## isoamyl acetate

*In training set.* Catalog descriptors (1 row(s) with this stereo-free structure): `isoamyl acetate: banana;fruity;pear;sweet`

```
SMILES: CC(=O)OCCC(C)C
Training membership: in training data (memorization possible)
Scores are model confidence, not calibrated probabilities.
 1. banana           0.993
 2. fruity           0.922
 3. pear             0.890
 4. pineapple        0.803
 5. rose             0.557
 6. sharp            0.551
 7. apple            0.518
 8. ethereal         0.511
 9. sweet            0.477
10. winey            0.467
```

## geraniol

*In training set.* Catalog descriptors (2 row(s) with this stereo-free structure): `geraniol: floral;rose;sweet`; `nerol: fresh;rose;sweet`

```
SMILES: CC(C)=CCC/C(C)=C/CO
Training membership: in training data (memorization possible)
Scores are model confidence, not calibrated probabilities.
 1. rose             0.956
 2. floral           0.866
 3. sweet            0.752
 4. fresh            0.749
 5. oily             0.613
 6. green            0.294
 7. citrus           0.242
 8. leafy            0.225
 9. fruity           0.220
10. balsamic         0.205
```

## limonene

*In training set.* Catalog descriptors (3 row(s) with this stereo-free structure): `limonene: citrus;gasoline`; `(-)-limonene: herbal;orange`; `d-limonene: citrus;fresh;gasoline;orange;sweet`

```
SMILES: CC1=CCC(CC1)C(=C)C
Training membership: in training data (memorization possible)
Scores are model confidence, not calibrated probabilities.
 1. gasoline         0.979
 2. orange           0.972
 3. citrus           0.958
 4. herbal           0.884
 5. fresh            0.683
 6. sweet            0.644
 7. spicy            0.466
 8. woody            0.325
 9. mint             0.323
10. tropical         0.279
```

## dimethyl sulfide

*In training set.* Catalog descriptors (1 row(s) with this stereo-free structure): `dimethyl sulfide: cabbage;pungent;vegetable`

```
SMILES: CSC
Training membership: in training data (memorization possible)
Scores are model confidence, not calibrated probabilities.
 1. cabbage          0.973
 2. sulfurous        0.916
 3. vegetable        0.880
 4. pungent          0.862
 5. onion            0.849
 6. meaty            0.766
 7. garlic           0.643
 8. savory           0.577
 9. alliaceous       0.515
10. tropical         0.413
```

## isovanillin

*In training set.* Catalog descriptors (1 row(s) with this stereo-free structure): `3-hydroxy-4-methoxybenzaldehyde: floral;hay;herbal;vanilla`

```
SMILES: O=Cc1ccc(OC)c(O)c1
Training membership: in training data (memorization possible)
Scores are model confidence, not calibrated probabilities.
 1. vanilla          0.999
 2. hay              0.972
 3. medicinal        0.955
 4. phenolic         0.829
 5. herbal           0.778
 6. floral           0.684
 7. sweet            0.641
 8. woody            0.503
 9. smoky            0.224
10. spicy            0.173
```

## 5-propylvanillin

*Not in dataset (prediction unvalidated).*

```
SMILES: CCCc1cc(C=O)cc(OC)c1O
Training membership: Not found in training data
This prediction is unvalidated: there is no ground truth for this molecule, close structural analogs may exist in the training set, and scores are uncalibrated model confidence.
Scores are model confidence, not calibrated probabilities.
 1. spicy            0.965
 2. balsamic         0.960
 3. smoky            0.807
 4. floral           0.676
 5. vanilla          0.660
 6. sweet            0.587
 7. milky            0.547
 8. creamy           0.511
 9. phenolic         0.320
10. medicinal        0.313
```

## ibuprofen

*Not in dataset (prediction unvalidated).*

```
SMILES: CC(C)Cc1ccc(cc1)C(C)C(=O)O
Training membership: Not found in training data
This prediction is unvalidated: there is no ground truth for this molecule, close structural analogs may exist in the training set, and scores are uncalibrated model confidence.
Scores are model confidence, not calibrated probabilities.
 1. floral           0.943
 2. sweet            0.747
 3. balsamic         0.694
 4. earthy           0.643
 5. spicy            0.578
 6. green            0.554
 7. herbal           0.283
 8. mint             0.278
 9. vegetable        0.158
10. leafy            0.148
```

Note: the label set has no 'odorless' class, so the model always returns some descriptors with nonzero score, even for molecules (such as ibuprofen) that are not regarded as odorants.
