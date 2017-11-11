# voterlist-extractor
Simple script to extract into a database the names of registered voters from the website of the Election Commission of Nepal
<br/><br/>
Tips for querying the large database(~ 5 GB) that will be spit out by the script:<br/>
<p>
+Create indices for the columns you will be querying before running the actual queries on those columns.
  E.g. CREATE INDEX IDX_VoterName ON AllVoters (VoterName)
  </p>
<p>
+Test how the SQLite query engine is going to execute your query by prefixing the query with EXPLAIN QUERY PLAN <br/>
-Avoid table scan at all costs as they can take tens of minutes, try to use indexes you've created for any query and if your query doesn't include the indexed column, index it right away and then run query on it
</p>
<p>
+If the SQLite query engine doesn't seem to be planning to use the indexes you've created(verify using EXPLAIN QUERY PLAN), you can force the use of indexes by appending ORDER BY SomeColumnName to a query provided the column SomeColumnName has a related index
</p>
