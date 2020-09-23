# Complexity Calculations

Economic Complexity studies the geography and dynamics of economic activities using methods inspired in ideas from complex systems, networks, and computer science.

## Functions

### RCA

The *Revealed Comparative Advantage* (RCA) is an index introduced by Balassa (1965), which is used to evaluate the main products to be exported by a country, and their comparative advantages in relation to the level of world exports (Hidalgo et al., 2007).

This function requires a pivot table using a geographic index, columns with the categories to be evaluated and the measurement of the data as values.

#### Note: It is important to note that the index always has to be geography.

For example:
`pd.pivot_table(df, index=[index], columns=[columns], values=values).reset_index().set_index(index).dropna(axis=1, how="all").fillna(0).astype(float) `

where in world exports: 
* *index*: countries ids 
* *columns*: products ids 
* *values*: trade value 

Finally the function returns a pivot table with RCA in the *values*

#### Note: To display these values ​​the matrix must be transformed into a dataframe with tidy format as shown below.
`df_rca = rca(pivot_table).unstack().reset_index(name="RCA")`

### Proximity

Hidalgo et al. (2007), introduces the *Proximity* index which measures the minimum probability that a country has comparative advantages in the export of a product *i*, given that it has comparative advantages in a product *j*.

This function only needs the pivot table obtained from the RCA function and returns a square matrix with the proximity between the elements.

Using the same example above, the function returns a table with the identifiers of the products for each column and row, and the values ​​at the intersection correspond to the proximity.

#### Note: This table is used in other complexity calculations such as the *Relatedness*

### Relatedness 

Usually, scholars measure *Relatedness* between a location and an economic activity to predict the probability that a region will enter or exit that activity in the future. The fact that the growth of an activity in a location is correlated with relatedness is known as The Principle of Relatedness introduced by Hidalgo et al. (2018), which consists of a statistical law that tells us that the probability that a location (a country, city, or region), enters an economic activity (e.g. a product, industry, technology), grows with the number of related activities present in a location.

This function needs two parameters:

1.- The pivot table obtained from the RCA function
2.- The matrix obtained from the Proximity function

Finally, this function returns a matrix with the probability that a location generates comparative advantages in a economic activity.

#### Note: It is important to clear that as in the calculation of the RCA, to show these values ​​the matrix must be transformed into a dataframe with tidy format as shown below.
`relatedness(RCA, Proximity).unstack().reset_index(name="Relatedness")`

### ECI and PCI 

Hidalgo & Hausmann (2009), calculate the economic complexity indices from the reflections method, which is defined based on a red bipartite that contains a symmetric set of variables whose nodes correspond to countries and products.

For ECI and PCI calculation use the *complexity* function. This function only needs one parameter, corresponding to the pivot table obtained with the RCA function.

This function only needs one parameter, corresponding to the pivot table obtained with the RCA function and returns two series, the first corresponds to the ECI that provides the complexity of a location and the second to the PCI related to the complexity of an economic activity.

#### Note: To display these values, the series must be transformed into a dataframe in an tidy format as shown below.
```
eci_value, pci_value = complexity(matriz_rca)

eci = eci.to_frame(name="ECI").reset_index() 
pci = pci.to_frame(name="PCI").reset_index()
```
### Cross-proximity

Catalan et al. (2020) introduced the *cross-proximity* index in order to measure the minimum probability that a country presents comparative advantages in a patent in a given area given that it has comparative advantages in an area of ​​knowledge, or vice versa, where values ​​that are more close to unity indicate a stronger relationship between the patent area and the knowledge area.

This function requires two parameters, in this order:

1.- `rcas_a`: The pivot table obtained from the RCA function for a one characteristic to evaluate 
2.- `rcas_b`: The pivot table obtained from the RCA function for the other characteristic to evaluate 

Finally, this function returns a matrix with the proximity between the two types of elements evaluated that can be used in the calculation of the *cross-relatedness*.

#### Note: * These characteristics can't be the location
####       * The order of the parameters is important because it influences the calculation of the *cross relatedness* 

### Cross-relatedness

Catalan et al. (2020) incorporated the concept of cross-relatedness in order to quantify the relationship between scientific fields in the development of new technologies in a country. The density crossing takes values ​​between zero and one, mathematically it corresponds to the average cross proximity of a technology  and the scientific knowledge of a country during the period of time.

This function requires two parameters, in this order:

1.- `rcas_a`: The pivot table obtained from the RCA function for the main characteristic to be evaluated
2.- `cross_proximity`: The pivot table obtained from the cross-prximity function

Finally, this function returns a matrix with the probability that a location generates comparative advantages in the characteristic to be evaluated considering its proximity with the other evaluated characteristic.

#### Note: * It's important to be consistent with the name of the variables when calculating cross-proximity and cross-relatedness
####       * To display these values, the series must be transformed into a dataframe in an tidy format as shown below.
`relatedness(rcas_a, cross_proximity).unstack().reset_index(name="cross_Relatedness")`























