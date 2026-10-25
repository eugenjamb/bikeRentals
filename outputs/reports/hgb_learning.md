# How the selected model learned

Algorithm: Histogram Gradient Boosting regression. It starts with a constant prediction,
then adds regression trees that correct errors in the current ensemble. Learning rate scales
each tree's contribution. Here there are 200 iterations. This is tree boosting, not
neural-network epochs or pretrained-model fine-tuning. Model fitting minimizes squared error;
we monitor MAE because MAE is the model-selection metric, so MAE need not fall at every step.

## Training versus validation

Each curve averages three folds. Preprocessing and the model are refitted using only each
fold's training period. Validation predictions use earlier observed demand as history.

| Boosting stage | Mean training MAE | Mean validation MAE |
| --- | ---: | ---: |
| After first tree | 119.77 | 180.58 |
| After 200 trees | 15.24 | 31.60 |

Training error measures fit to examples used for learning. Validation error measures later
hours not used to fit that fold. Lower validation error indicates more useful predictions.
A growing training/validation gap can indicate overfitting, but this plot alone does not
establish a model's generalization performance. These folds already selected the parameters.
We do not change the iteration count based on this diagnostic plot.

The saved deployment-candidate pipeline is separately refitted on all eligible development
hours. This plot describes fold models, not a score from that final refit on its own training data.
Final-test results are recorded separately; this learning plot uses development folds only. Inspect actual-versus-predicted plots and the first-day
prediction examples in `validation_closeness.md` to connect these curves to concrete errors.
