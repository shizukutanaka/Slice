# Photo benchmark fixtures

These historical NASA photographs are used here for an informational
benchmark. NASA does not endorse Slice. The photographs are credited below
and are not licensed by Slice under its MIT license. See
[NASA's Images and Media Usage Guidelines](https://www.nasa.gov/nasa-brand-center/images-and-media/)
for terms governing other uses, including use of identifiable people.

| Fixture | Source and credit | Scene |
|---|---|---|
| `nasa-s63-01755.png` | [S63-01755](https://images.nasa.gov/details/S63-01755) (NASA) | Standing portrait with a nearly uniform background and a helmet obscuring part of the arms |
| `nasa-as15-88-11866.png` | [AS15-88-11866](https://images.nasa.gov/details/as15-88-11866) (NASA / David R. Scott) | Standing, saluting figure against terrain and equipment |

Both files are the NASA catalog's small JPEG renditions converted to PNG
and resized to 420 pixels on the longest side. No backgrounds were removed.
`manifest.json` contains approximate visible joint centers manually placed
on those resized images, not inferred by Slice. Occluded or ambiguous points
are omitted; `_l` and `_r` follow the image-side convention for the frontal
figures in Slice's benchmark. The labels are approximate because both
subjects wear bulky suits; the two images are not representative of
general-purpose pose accuracy.
