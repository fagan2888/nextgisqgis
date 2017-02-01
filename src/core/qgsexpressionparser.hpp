/* A Bison parser, made by GNU Bison 3.0.4.  */

/* Bison interface for Yacc-like parsers in C

   Copyright (C) 1984, 1989-1990, 2000-2015 Free Software Foundation, Inc.

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.  */

/* As a special exception, you may create a larger work that contains
   part or all of the Bison parser skeleton and distribute that work
   under terms of your choice, so long as that work isn't itself a
   parser generator using the skeleton or a modified version thereof
   as a parser skeleton.  Alternatively, if you modify or redistribute
   the parser skeleton itself, you may (at your option) remove this
   special exception, which will cause the skeleton and the resulting
   Bison output files to be licensed under the GNU General Public
   License without this special exception.

   This special exception was added by the Free Software Foundation in
   version 2.2 of Bison.  */

#ifndef YY_EXP_QGSEXPRESSIONPARSER_HPP_INCLUDED
# define YY_EXP_QGSEXPRESSIONPARSER_HPP_INCLUDED
/* Debug traces.  */
#ifndef YYDEBUG
# define YYDEBUG 0
#endif
#if YYDEBUG
extern int exp_debug;
#endif

/* Token type.  */
#ifndef YYTOKENTYPE
# define YYTOKENTYPE
  enum yytokentype
  {
    OR = 258,
    AND = 259,
    EQ = 260,
    NE = 261,
    LE = 262,
    GE = 263,
    LT = 264,
    GT = 265,
    REGEXP = 266,
    LIKE = 267,
    IS = 268,
    PLUS = 269,
    MINUS = 270,
    MUL = 271,
    DIV = 272,
    INTDIV = 273,
    MOD = 274,
    CONCAT = 275,
    POW = 276,
    NOT = 277,
    IN = 278,
    NUMBER_FLOAT = 279,
    NUMBER_INT = 280,
    BOOLEAN = 281,
    NULLVALUE = 282,
    CASE = 283,
    WHEN = 284,
    THEN = 285,
    ELSE = 286,
    END = 287,
    STRING = 288,
    COLUMN_REF = 289,
    FUNCTION = 290,
    SPECIAL_COL = 291,
    VARIABLE = 292,
    COMMA = 293,
    Unknown_CHARACTER = 294,
    UMINUS = 295
  };
#endif

/* Value type.  */
#if ! defined YYSTYPE && ! defined YYSTYPE_IS_DECLARED

union YYSTYPE
{
//#line 77 "/home/bishop/work/projects/nextgisqgis/src/core/qgsexpressionparser.yy" /* yacc.c:1909  */

  QgsExpression::Node* node;
  QgsExpression::NodeList* nodelist;
  double numberFloat;
  int    numberInt;
  bool   boolVal;
  QString* text;
  QgsExpression::BinaryOperator b_op;
  QgsExpression::UnaryOperator u_op;
  QgsExpression::WhenThen* whenthen;
  QgsExpression::WhenThenList* whenthenlist;

//#line 108 "/home/bishop/work/projects/nextgisqgis/src/core/qgsexpressionparser.hpp" /* yacc.c:1909  */
};

typedef union YYSTYPE YYSTYPE;
# define YYSTYPE_IS_TRIVIAL 1
# define YYSTYPE_IS_DECLARED 1
#endif



int exp_parse (expression_parser_context* parser_ctx);

#endif /* !YY_EXP_QGSEXPRESSIONPARSER_HPP_INCLUDED  */
