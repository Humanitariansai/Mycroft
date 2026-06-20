CREATE CONSTRAINT company_name IF NOT EXISTS
  FOR (c:Company) REQUIRE c.name IS UNIQUE;

CREATE CONSTRAINT investor_name IF NOT EXISTS
  FOR (i:Investor) REQUIRE i.name IS UNIQUE;

CREATE INDEX company_stage IF NOT EXISTS
  FOR (c:Company) ON (c.stage);

CREATE INDEX company_founded IF NOT EXISTS
  FOR (c:Company) ON (c.founded_year);
